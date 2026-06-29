#include "DetectorMessenger.hh"

#include "DetectorConstruction.hh"

#include "G4UIcmdWithADouble.hh"
#include "G4UIcmdWithADoubleAndUnit.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIcmdWithAnInteger.hh"
#include "G4UIcmdWithoutParameter.hh"
#include "G4UIdirectory.hh"

DetectorMessenger::DetectorMessenger(DetectorConstruction* detector) : fDetector(detector)
{
  fGeometryDirectory = new G4UIdirectory("/shield/geometry/");
  fGeometryDirectory->SetGuidance("Shield geometry controls.");

  fMaterialDirectory = new G4UIdirectory("/shield/material/");
  fMaterialDirectory->SetGuidance("Shield material controls.");

  fAddMassFractionMaterialCommand = new G4UIcmdWithAString("/shield/material/addMassFraction", this);
  fAddMassFractionMaterialCommand->SetGuidance(
    "Define a material: name density_g_cm3 element:fraction [element:fraction ...].");
  fAddMassFractionMaterialCommand->SetParameterName("spec", false);

  fClearLayersCommand = new G4UIcmdWithoutParameter("/shield/geometry/clearLayers", this);
  fClearLayersCommand->SetGuidance("Remove all shield layers before adding a new stack.");

  fAddLayerCommand = new G4UIcmdWithAString("/shield/geometry/addLayer", this);
  fAddLayerCommand->SetGuidance("Add a layer: material thickness unit [divisions].");
  fAddLayerCommand->SetParameterName("spec", false);

  fTransverseSizeCommand = new G4UIcmdWithADoubleAndUnit("/shield/geometry/transverseSize", this);
  fTransverseSizeCommand->SetGuidance("Set square transverse shield size.");
  fTransverseSizeCommand->SetParameterName("size", false);
  fTransverseSizeCommand->SetDefaultUnit("cm");

  // ── RVE geometry commands ────────────────────────────────────────────────
  fRVEDirectory = new G4UIdirectory("/shield/rve/");
  fRVEDirectory->SetGuidance("Explicit-RVE nanoparticle geometry controls (regimes B and C).");

  fGeometryModeCommand = new G4UIcmdWithAString("/shield/geometry/mode", this);
  fGeometryModeCommand->SetGuidance(
    "Set geometry mode: slab | rve_explicit | rve_multiunion.");
  fGeometryModeCommand->SetParameterName("mode", false);

  fRVEMatrixMaterialCommand = new G4UIcmdWithAString("/shield/rve/matrixMaterial", this);
  fRVEMatrixMaterialCommand->SetGuidance("Matrix material name for RVE.");
  fRVEMatrixMaterialCommand->SetParameterName("name", false);

  fRVEFillerMaterialCommand = new G4UIcmdWithAString("/shield/rve/fillerMaterial", this);
  fRVEFillerMaterialCommand->SetGuidance("Filler material name for RVE nanoparticles.");
  fRVEFillerMaterialCommand->SetParameterName("name", false);

  fRVESideLengthCommand = new G4UIcmdWithADoubleAndUnit("/shield/rve/sideLength", this);
  fRVESideLengthCommand->SetGuidance("Cubic RVE side length.");
  fRVESideLengthCommand->SetParameterName("length", false);
  fRVESideLengthCommand->SetDefaultUnit("nm");

  fRVEParticleRadiusCommand = new G4UIcmdWithADoubleAndUnit("/shield/rve/particleRadius", this);
  fRVEParticleRadiusCommand->SetGuidance("Nanoparticle sphere radius.");
  fRVEParticleRadiusCommand->SetParameterName("radius", false);
  fRVEParticleRadiusCommand->SetDefaultUnit("nm");

  fRVEVolumeFractionCommand = new G4UIcmdWithADouble("/shield/rve/volumeFraction", this);
  fRVEVolumeFractionCommand->SetGuidance("Filler volume fraction (0–1).");
  fRVEVolumeFractionCommand->SetParameterName("phi", false);

  fRVEMaxParticlesCommand = new G4UIcmdWithAnInteger("/shield/rve/maxParticles", this);
  fRVEMaxParticlesCommand->SetGuidance("Maximum number of nanoparticles to place.");
  fRVEMaxParticlesCommand->SetParameterName("n", false);

  fRVESeedCommand = new G4UIcmdWithAnInteger("/shield/rve/seed", this);
  fRVESeedCommand->SetGuidance("Random seed for RSA particle placement.");
  fRVESeedCommand->SetParameterName("seed", false);
}

DetectorMessenger::~DetectorMessenger()
{
  delete fRVESeedCommand;
  delete fRVEMaxParticlesCommand;
  delete fRVEVolumeFractionCommand;
  delete fRVEParticleRadiusCommand;
  delete fRVESideLengthCommand;
  delete fRVEFillerMaterialCommand;
  delete fRVEMatrixMaterialCommand;
  delete fGeometryModeCommand;
  delete fRVEDirectory;
  delete fTransverseSizeCommand;
  delete fAddLayerCommand;
  delete fClearLayersCommand;
  delete fAddMassFractionMaterialCommand;
  delete fMaterialDirectory;
  delete fGeometryDirectory;
}

void DetectorMessenger::SetNewValue(G4UIcommand* command, G4String value)
{
  if (command == fClearLayersCommand) {
    fDetector->ClearLayers();
    return;
  }
  if (command == fAddLayerCommand) {
    fDetector->AddLayerCommand(value);
    return;
  }
  if (command == fAddMassFractionMaterialCommand) {
    fDetector->AddMassFractionMaterialCommand(value);
    return;
  }
  if (command == fTransverseSizeCommand) {
    fDetector->SetTransverseSize(fTransverseSizeCommand->GetNewDoubleValue(value));
    return;
  }
  // RVE commands
  if (command == fGeometryModeCommand) {
    fDetector->SetGeometryMode(value);
    return;
  }
  if (command == fRVEMatrixMaterialCommand) {
    fDetector->SetRVEMatrixMaterial(value);
    return;
  }
  if (command == fRVEFillerMaterialCommand) {
    fDetector->SetRVEFillerMaterial(value);
    return;
  }
  if (command == fRVESideLengthCommand) {
    fDetector->SetRVESideLength(fRVESideLengthCommand->GetNewDoubleValue(value));
    return;
  }
  if (command == fRVEParticleRadiusCommand) {
    fDetector->SetRVEParticleRadius(fRVEParticleRadiusCommand->GetNewDoubleValue(value));
    return;
  }
  if (command == fRVEVolumeFractionCommand) {
    fDetector->SetRVEVolumeFraction(fRVEVolumeFractionCommand->GetNewDoubleValue(value));
    return;
  }
  if (command == fRVEMaxParticlesCommand) {
    fDetector->SetRVEMaxParticles(fRVEMaxParticlesCommand->GetNewIntValue(value));
    return;
  }
  if (command == fRVESeedCommand) {
    fDetector->SetRVESeed(fRVESeedCommand->GetNewIntValue(value));
  }
}