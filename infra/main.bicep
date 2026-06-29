@description('Deployment location for all resources.')
param location string = resourceGroup().location

@description('Global name prefix. Keep it short and unique per environment.')
param appNamePrefix string

@description('App Service plan SKU name.')
@allowed([
  'B1'
  'S1'
  'P1v3'
])
param appServiceSku string = 'S1'

@description('Set to true to enable App Service Easy Auth (Microsoft Entra ID).')
param enableEasyAuth bool = true

@description('Microsoft Entra tenant auth endpoint, for example: https://login.microsoftonline.com/<tenant-id>/v2.0')
param aadAuthority string = ''

@description('App registration (client) ID used by App Service Easy Auth.')
param aadClientId string = ''

@secure()
@description('Client secret value for the App registration. Leave empty when enableEasyAuth=false.')
param aadClientSecret string = ''

@description('Queue name for incoming simulation jobs.')
param jobsQueueName string = 'simulation-jobs'

@description('Maximum number of times a message is dequeued before it is moved to the dead-letter (poison) queue. Must be >= 1.')
@minValue(1)
param maxDequeueCount int = 5

@description('Blob container for study input payloads.')
param inputContainerName string = 'simulation-input'

@description('Blob container for simulation result artifacts.')
param outputContainerName string = 'simulation-output'

@description('Deploy a VNet, private endpoints for Storage (blob + queue), and VNet integration for the App Service. Set false for development deployments. Requires an S1 or P1v3 plan for VNet integration.')
param enablePrivateEndpoints bool = false

@description('VNet address space CIDR. Ignored when enablePrivateEndpoints=false.')
param vnetAddressPrefix string = '10.0.0.0/16'

@description('Subnet CIDR for App Service VNet integration (/26 minimum). Ignored when enablePrivateEndpoints=false.')
param appSubnetPrefix string = '10.0.0.0/24'

@description('Subnet CIDR for private endpoints. Ignored when enablePrivateEndpoints=false.')
param peSubnetPrefix string = '10.0.1.0/24'

var planName = '${appNamePrefix}-asp'
var webAppName = '${appNamePrefix}-web'
var appInsightsName = '${appNamePrefix}-appi'
var storageBase = toLower(replace(appNamePrefix, '-', ''))
var storageAccountName = substring('${storageBase}${uniqueString(resourceGroup().id, appNamePrefix)}', 0, 24)
var vnetName = '${appNamePrefix}-vnet'
var appSubnetName = 'app-integration-snet'
var peSubnetName = 'private-endpoints-snet'
// Use environment() so the template is portable across Azure sovereign clouds.
var blobDnsZoneName = 'privatelink.blob.${environment().suffixes.storage}'
var queueDnsZoneName = 'privatelink.queue.${environment().suffixes.storage}'

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    IngestionMode: 'ApplicationInsights'
  }
}

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  sku: {
    name: appServiceSku
    tier: startsWith(appServiceSku, 'P') ? 'PremiumV3' : (startsWith(appServiceSku, 'S') ? 'Standard' : 'Basic')
    size: appServiceSku
    capacity: 1
  }
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      healthCheckPath: '/_stcore/health'
      linuxFxVersion: 'PYTHON|3.11'
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
        {
          name: 'AZURE_QUEUE_NAME'
          value: jobsQueueName
        }
        {
          name: 'SHIELDLAB_WORKER_MAX_DEQUEUE_COUNT'
          value: string(maxDequeueCount)
        }
      ]
    }
  }
}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
    networkAcls: {
      defaultAction: enablePrivateEndpoints ? 'Deny' : 'Allow'
      bypass: 'AzureServices'
    }
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

resource inputContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: inputContainerName
  properties: {
    publicAccess: 'None'
  }
}

resource outputContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: outputContainerName
  properties: {
    publicAccess: 'None'
  }
}

resource queueService 'Microsoft.Storage/storageAccounts/queueServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

resource jobsQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  parent: queueService
  name: jobsQueueName
}

// Dead-letter (poison) queue: receives messages that exceed maxDequeueCount retries.
resource poisonQueue 'Microsoft.Storage/storageAccounts/queueServices/queues@2023-05-01' = {
  parent: queueService
  name: '${jobsQueueName}-poison'
}

// ── Private networking (enablePrivateEndpoints=true) ──────────────────────────
// When enabled:
//   • A dedicated VNet is created with two subnets:
//       app-integration-snet  — App Service outbound VNet integration
//       private-endpoints-snet — hosts the blob + queue private endpoints
//   • Storage public network access is set to Deny (only PE traffic allowed).
//   • Private DNS zones privatelink.blob/queue.core.windows.net are linked
//     to the VNet so DNS resolves to private IPs inside the VNet.
// Default is false so that development deployments remain unaffected.

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = if (enablePrivateEndpoints) {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [vnetAddressPrefix]
    }
    subnets: [
      {
        name: appSubnetName
        properties: {
          addressPrefix: appSubnetPrefix
          // Required for App Service Swift VNet integration.
          delegations: [
            {
              name: 'appservice-delegation'
              properties: {
                serviceName: 'Microsoft.Web/serverFarms'
              }
            }
          ]
        }
      }
      {
        name: peSubnetName
        properties: {
          addressPrefix: peSubnetPrefix
          // Must be Disabled to place private endpoints in this subnet.
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

// App Service outbound VNet integration (Swift). Requires S1 / P1v3 or higher.
resource webAppVnetConfig 'Microsoft.Web/sites/networkConfig@2023-12-01' = if (enablePrivateEndpoints) {
  parent: webApp
  name: 'virtualNetwork'
  properties: {
    subnetResourceId: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, appSubnetName)
    swiftSupported: true
  }
  dependsOn: [vnet]
}

// ── Private DNS zones ─────────────────────────────────────────────────────────

resource blobDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enablePrivateEndpoints) {
  name: blobDnsZoneName
  location: 'global'
}

resource queueDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enablePrivateEndpoints) {
  name: queueDnsZoneName
  location: 'global'
}

resource blobDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enablePrivateEndpoints) {
  parent: blobDnsZone
  name: '${vnetName}-blob'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: resourceId('Microsoft.Network/virtualNetworks', vnetName)
    }
  }
  dependsOn: [vnet]
}

resource queueDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enablePrivateEndpoints) {
  parent: queueDnsZone
  name: '${vnetName}-queue'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: resourceId('Microsoft.Network/virtualNetworks', vnetName)
    }
  }
  dependsOn: [vnet]
}

// ── Private endpoints ─────────────────────────────────────────────────────────

resource blobPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = if (enablePrivateEndpoints) {
  name: '${storageAccountName}-blob-pe'
  location: location
  properties: {
    subnet: {
      id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, peSubnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${storageAccountName}-blob-plsc'
        properties: {
          privateLinkServiceId: storageAccount.id
          groupIds: ['blob']
        }
      }
    ]
  }
  dependsOn: [vnet]
}

resource queuePrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = if (enablePrivateEndpoints) {
  name: '${storageAccountName}-queue-pe'
  location: location
  properties: {
    subnet: {
      id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, peSubnetName)
    }
    privateLinkServiceConnections: [
      {
        name: '${storageAccountName}-queue-plsc'
        properties: {
          privateLinkServiceId: storageAccount.id
          groupIds: ['queue']
        }
      }
    ]
  }
  dependsOn: [vnet]
}

// DNS zone groups wire private endpoints to private DNS zones so that
// FQDNs resolve to the private NIC IPs automatically.
resource blobPeDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = if (enablePrivateEndpoints) {
  parent: blobPrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'blob'
        properties: {
          privateDnsZoneId: blobDnsZone.id
        }
      }
    ]
  }
}

resource queuePeDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = if (enablePrivateEndpoints) {
  parent: queuePrivateEndpoint
  name: 'default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'queue'
        properties: {
          privateDnsZoneId: queueDnsZone.id
        }
      }
    ]
  }
}

resource authSettings 'Microsoft.Web/sites/config@2023-12-01' = if (enableEasyAuth) {
  parent: webApp
  name: 'authsettingsV2'
  properties: {
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          openIdIssuer: aadAuthority
          clientId: aadClientId
          clientSecretSettingName: 'AAD_CLIENT_SECRET'
        }
        validation: {
          allowedAudiences: [
            'api://${aadClientId}'
            aadClientId
          ]
        }
      }
    }
    login: {
      tokenStore: {
        enabled: true
      }
    }
    platform: {
      enabled: true
      runtimeVersion: '~1'
    }
  }
}

resource secretSetting 'Microsoft.Web/sites/config@2023-12-01' = if (enableEasyAuth) {
  parent: webApp
  name: 'appsettings'
  properties: {
    AAD_CLIENT_SECRET: aadClientSecret
  }
}

output webAppName string = webApp.name
output webAppDefaultHostName string = webApp.properties.defaultHostName
output storageAccountName string = storageAccount.name
output jobsQueueName string = jobsQueueName
output poisonQueueName string = '${jobsQueueName}-poison'
output inputContainerName string = inputContainerName
output outputContainerName string = outputContainerName
output vnetName string = enablePrivateEndpoints ? vnetName : ''
output blobPrivateEndpointName string = enablePrivateEndpoints ? '${storageAccountName}-blob-pe' : ''
output queuePrivateEndpointName string = enablePrivateEndpoints ? '${storageAccountName}-queue-pe' : ''
