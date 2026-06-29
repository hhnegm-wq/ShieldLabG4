#include "MaterialRegistry.hh"

#include "G4Element.hh"
#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

#include <cmath>
#include <sstream>
#include <vector>

namespace
{
struct ElementFraction
{
  G4String symbol;
  G4double fraction = 0.;
};

ElementFraction ParseElementFraction(const G4String& token)
{
  const auto separator = token.find(':');
  if (separator == std::string::npos) {
    G4Exception("MaterialRegistry::ParseElementFraction", "ShieldLabMat001", FatalException,
                ("Expected element:fraction token, got " + token).c_str());
  }
  ElementFraction value;
  value.symbol = token.substr(0, separator);
  value.fraction = std::stod(token.substr(separator + 1));
  return value;
}
}

MaterialRegistry* MaterialRegistry::Instance()
{
  static MaterialRegistry registry;
  return &registry;
}

void MaterialRegistry::AddMassFractionMaterialCommand(const G4String& spec)
{
  std::istringstream stream(spec);
  G4String materialName;
  G4double density = 0.;
  stream >> materialName >> density;
  if (!stream || density <= 0.) {
    G4Exception("MaterialRegistry::AddMassFractionMaterialCommand", "ShieldLabMat002", JustWarning,
                "Expected: name density_g_cm3 element:fraction [element:fraction ...]");
    return;
  }

  std::vector<ElementFraction> components;
  G4String token;
  G4double fractionSum = 0.;
  while (stream >> token) {
    auto component = ParseElementFraction(token);
    if (component.fraction <= 0.) {
      G4Exception("MaterialRegistry::AddMassFractionMaterialCommand", "ShieldLabMat003", JustWarning,
                  "Element fractions must be positive.");
      return;
    }
    fractionSum += component.fraction;
    components.push_back(component);
  }

  if (components.empty()) {
    G4Exception("MaterialRegistry::AddMassFractionMaterialCommand", "ShieldLabMat004", JustWarning,
                "At least one element:fraction component is required.");
    return;
  }
  if (std::abs(fractionSum - 1.0) > 1.e-6) {
    G4Exception("MaterialRegistry::AddMassFractionMaterialCommand", "ShieldLabMat005", JustWarning,
                "Mass fractions must sum to 1.0.");
    return;
  }

  if (G4Material::GetMaterial(materialName, false)) {
    G4cout << "ShieldLab-G4 material already exists: " << materialName << G4endl;
    return;
  }

  auto* nist = G4NistManager::Instance();
  auto* material = new G4Material(materialName, density * g / cm3, components.size());
  for (const auto& component : components) {
    auto* element = nist->FindOrBuildElement(component.symbol);
    if (!element) {
      G4Exception("MaterialRegistry::AddMassFractionMaterialCommand", "ShieldLabMat006", FatalException,
                  ("Unknown element symbol: " + component.symbol).c_str());
    }
    material->AddElement(element, component.fraction);
  }

  G4cout << "ShieldLab-G4 material defined: " << materialName << " density " << density
         << " g/cm3" << G4endl;
}

G4Material* MaterialRegistry::FindOrBuildMaterial(const G4String& materialName) const
{
  if (auto* material = G4Material::GetMaterial(materialName, false)) {
    return material;
  }
  return G4NistManager::Instance()->FindOrBuildMaterial(materialName);
}