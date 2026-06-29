#include "DetectorConstruction.hh"

#include "DetectorMessenger.hh"
#include "MaterialRegistry.hh"
#include "NanoParticleParameterisation.hh"

#include "G4Box.hh"
#include "G4GeometryManager.hh"
#include "G4LogicalVolume.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4Material.hh"
#include "G4MultiFunctionalDetector.hh"
#include "G4MultiUnion.hh"
#include "G4NistManager.hh"
#include "G4PSDoseDeposit.hh"
#include "G4PSEnergyDeposit.hh"
#include "G4PVParameterised.hh"
#include "G4PVPlacement.hh"
#include "G4PhysicalConstants.hh"
#include "G4PhysicalVolumeStore.hh"
#include "G4RotationMatrix.hh"
#include "G4RunManager.hh"
#include "G4SDManager.hh"
#include "G4Sphere.hh"
#include "G4SolidStore.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4Transform3D.hh"
#include "G4UnitsTable.hh"
#include "G4VPhysicalVolume.hh"
#include "G4ios.hh"

#include <cfloat>
#include <cmath>
#include <random>
#include <sstream>

DetectorConstruction::DetectorConstruction()
{
  fTransverseSize = 10.0 * cm;
  fWorldPadding = 2.0 * cm;
  DefineDefaultMaterials();
  AddLayer("G4_Pb", 1.0 * cm, 1);
  fMessenger = new DetectorMessenger(this);
}

DetectorConstruction::~DetectorConstruction()
{
  delete fMessenger;
}

void DetectorConstruction::DefineDefaultMaterials()
{
  auto* nist = G4NistManager::Instance();
  nist->FindOrBuildMaterial("G4_AIR");
  nist->FindOrBuildMaterial("G4_WATER");
  nist->FindOrBuildMaterial("G4_Al");
  nist->FindOrBuildMaterial("G4_Fe");
  nist->FindOrBuildMaterial("G4_Cu");
  nist->FindOrBuildMaterial("G4_W");
  nist->FindOrBuildMaterial("G4_Pb");
  nist->FindOrBuildMaterial("G4_CONCRETE");

  fWorldMaterial = new G4Material("ShieldLab_Galactic", 1., 1.008 * g / mole,
                                  universe_mean_density, kStateGas, 2.73 * kelvin,
                                  3.e-18 * pascal);
}

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  G4GeometryManager::GetInstance()->OpenGeometry();
  G4PhysicalVolumeStore::GetInstance()->Clean();
  G4LogicalVolumeStore::GetInstance()->Clean();
  G4SolidStore::GetInstance()->Clean();

  fLayerMaterials.clear();
  fSegmentLayerIndex.clear();
  for (const auto& layer : fLayers) {
    fLayerMaterials.push_back(ResolveMaterial(layer.materialName));
  }

  const G4double totalThickness = GetTotalThickness();
  fWorldHalfX = 0.5 * totalThickness + fWorldPadding;

  // World transverse: fTransverseSize for slab; fRVESideLength for RVE.
  const G4double worldTransverse =
    (fGeometryMode == GeometryMode::Slab) ? fTransverseSize : fRVESideLength;

  auto* solidWorld =
    new G4Box("World", fWorldHalfX, 0.5 * worldTransverse, 0.5 * worldTransverse);
  auto* logicWorld = new G4LogicalVolume(solidWorld, fWorldMaterial, "World");
  auto* physicalWorld = new G4PVPlacement(nullptr, {}, logicWorld, "World", nullptr, false, 0);

  if (fGeometryMode == GeometryMode::Slab) {
    BuildSlab(logicWorld);
  } else if (fGeometryMode == GeometryMode::RVEParameterised) {
    BuildRVEParameterised(logicWorld);
  } else {
    BuildRVEMultiUnion(logicWorld);
  }

  return physicalWorld;
}

void DetectorConstruction::BuildSlab(G4LogicalVolume* logicWorld)
{
  const G4double totalThickness = GetTotalThickness();
  G4double xFront = -0.5 * totalThickness;
  for (std::size_t index = 0; index < fLayers.size(); ++index) {
    const auto& layer = fLayers[index];
    const G4int divisions = std::max(1, layer.divisions);
    const G4double segmentThickness = layer.thickness / divisions;
    for (G4int division = 0; division < divisions; ++division) {
      const G4double xCenter = xFront + 0.5 * segmentThickness;
      std::ostringstream solidName;
      solidName << "LayerSolid_" << index << '_' << division;
      std::ostringstream logicalName;
      logicalName << "ShieldLayerLogical_" << index << '_' << division;
      auto* solidLayer = new G4Box(solidName.str(), 0.5 * segmentThickness, 0.5 * fTransverseSize,
                                   0.5 * fTransverseSize);
      auto* logicLayer = new G4LogicalVolume(solidLayer, fLayerMaterials[index], logicalName.str());
      const auto copyNumber = static_cast<G4int>(fSegmentLayerIndex.size());
      new G4PVPlacement(nullptr, G4ThreeVector(xCenter, 0., 0.), logicLayer, "ShieldLayer",
                        logicWorld, false, copyNumber);
      fSegmentLayerIndex.push_back(static_cast<G4int>(index));
      xFront += segmentThickness;
    }
  }
  G4cout << "\nShieldLab-G4 geometry (slab):" << G4endl;
  for (std::size_t index = 0; index < fLayers.size(); ++index) {
    G4cout << "  layer " << index + 1 << ": " << fLayers[index].materialName << ", "
           << G4BestUnit(fLayers[index].thickness, "Length") << ", divisions "
           << fLayers[index].divisions << G4endl;
  }
  G4cout << "  total thickness: " << G4BestUnit(totalThickness, "Length") << G4endl;
}

std::vector<G4ThreeVector> DetectorConstruction::ComputeRSAPositions(
    G4double sideLength, G4double particleRadius,
    G4double volumeFraction, G4int maxParticles, G4long seed)
{
  const G4double particleVol =
    (4.0 / 3.0) * CLHEP::pi * particleRadius * particleRadius * particleRadius;
  const G4double boxVol = sideLength * sideLength * sideLength;
  auto nTarget = static_cast<G4int>(std::round(volumeFraction * boxVol / particleVol));
  nTarget = std::max(0, std::min(nTarget, maxParticles));

  const G4double bound = 0.5 * sideLength - particleRadius;
  if (bound <= 0.0 || nTarget <= 0) {
    G4cout << "RVE RSA: no particles to place (bound=" << bound
           << ", nTarget=" << nTarget << ")" << G4endl;
    return {};
  }

  std::mt19937_64 rng(static_cast<std::uint64_t>(seed));
  std::uniform_real_distribution<double> dist(-bound, bound);

  const G4double minDist2 = (2.0 * particleRadius) * (2.0 * particleRadius);
  const G4int maxAttempts = nTarget * 1000;

  std::vector<G4ThreeVector> positions;
  positions.reserve(static_cast<std::size_t>(nTarget));

  for (G4int attempt = 0;
       static_cast<G4int>(positions.size()) < nTarget && attempt < maxAttempts;
       ++attempt)
  {
    G4ThreeVector candidate(dist(rng), dist(rng), dist(rng));
    bool overlap = false;
    for (const auto& existing : positions) {
      if ((candidate - existing).mag2() < minDist2) {
        overlap = true;
        break;
      }
    }
    if (!overlap) positions.push_back(candidate);
  }

  const G4double achieved =
    positions.empty() ? 0.0
                      : static_cast<double>(positions.size()) * particleVol / boxVol;
  G4cout << "RVE RSA: placed " << positions.size() << "/" << nTarget
         << "  achieved phi=" << achieved << G4endl;
  return positions;
}

void DetectorConstruction::BuildRVEParameterised(G4LogicalVolume* logicWorld)
{
  if (fRVESideLength <= 0.0 || fRVEParticleRadius <= 0.0 || fRVEVolumeFraction <= 0.0) {
    G4Exception("DetectorConstruction::BuildRVEParameterised", "ShieldLab010",
                JustWarning, "RVE parameters invalid; falling back to slab.");
    BuildSlab(logicWorld);
    return;
  }

  auto* matrixMat = ResolveMaterial(fRVEMatrixMaterialName);
  auto* fillerMat = ResolveMaterial(fRVEFillerMaterialName);

  // RVE host volume (matrix).
  const G4double L = fRVESideLength;
  auto* rveBox = new G4Box("RVEHost", 0.5 * L, 0.5 * L, 0.5 * L);
  auto* rveLogic = new G4LogicalVolume(rveBox, matrixMat, "RVEHost");
  new G4PVPlacement(nullptr, G4ThreeVector(0., 0., 0.), rveLogic, "RVEHost",
                    logicWorld, false, 0);

  // Filler sphere logical volume (shared by all parameterised copies).
  auto* npSolid = new G4Sphere("NPSphere", 0., fRVEParticleRadius,
                                0., CLHEP::twopi, 0., CLHEP::pi);
  auto* npLogic = new G4LogicalVolume(npSolid, fillerMat, "NPSphere");

  // RSA placement.
  auto positions = ComputeRSAPositions(L, fRVEParticleRadius,
                                       fRVEVolumeFraction, fRVEMaxParticles, fRVESeed);
  if (positions.empty()) {
    G4cout << "RVE RSA: no positions generated; RVE contains only matrix material." << G4endl;
    return;
  }

  auto* param = new NanoParticleParameterisation(positions);
  new G4PVParameterised("NPParam", npLogic, rveLogic, kUndefined,
                         param->GetNParticles(), param);

  G4cout << "\nShieldLab-G4 geometry (RVE parameterised):" << G4endl;
  G4cout << "  side:   " << G4BestUnit(L, "Length") << G4endl;
  G4cout << "  radius: " << G4BestUnit(fRVEParticleRadius, "Length") << G4endl;
  G4cout << "  placed: " << positions.size() << " particles" << G4endl;
}

void DetectorConstruction::BuildRVEMultiUnion(G4LogicalVolume* logicWorld)
{
  if (fRVESideLength <= 0.0 || fRVEParticleRadius <= 0.0 || fRVEVolumeFraction <= 0.0) {
    G4Exception("DetectorConstruction::BuildRVEMultiUnion", "ShieldLab011",
                JustWarning, "RVE parameters invalid; falling back to slab.");
    BuildSlab(logicWorld);
    return;
  }

  auto* matrixMat = ResolveMaterial(fRVEMatrixMaterialName);
  auto* fillerMat = ResolveMaterial(fRVEFillerMaterialName);

  const G4double L = fRVESideLength;
  auto* rveBox = new G4Box("RVEHost", 0.5 * L, 0.5 * L, 0.5 * L);
  auto* rveLogic = new G4LogicalVolume(rveBox, matrixMat, "RVEHost");
  new G4PVPlacement(nullptr, G4ThreeVector(0., 0., 0.), rveLogic, "RVEHost",
                    logicWorld, false, 0);

  auto positions = ComputeRSAPositions(L, fRVEParticleRadius,
                                       fRVEVolumeFraction, fRVEMaxParticles, fRVESeed);
  if (positions.empty()) {
    G4cout << "RVE RSA: no positions; RVE contains only matrix material." << G4endl;
    return;
  }

  // Build G4MultiUnion of all filler spheres.
  auto* fillerUnion = new G4MultiUnion("FillerUnion");
  auto* sphereTemplate = new G4Sphere("NPSphereTemplate", 0., fRVEParticleRadius,
                                       0., CLHEP::twopi, 0., CLHEP::pi);
  G4RotationMatrix identity;
  for (const auto& pos : positions) {
    G4Transform3D transform(identity, pos);
    fillerUnion->AddNode(*sphereTemplate, transform);
  }
  fillerUnion->Voxelize();

  auto* fillerLogic = new G4LogicalVolume(fillerUnion, fillerMat, "FillerMultiUnion");
  new G4PVPlacement(nullptr, G4ThreeVector(0., 0., 0.), fillerLogic,
                    "FillerMultiUnion", rveLogic, false, 0);

  G4cout << "\nShieldLab-G4 geometry (RVE MultiUnion):" << G4endl;
  G4cout << "  side:   " << G4BestUnit(L, "Length") << G4endl;
  G4cout << "  radius: " << G4BestUnit(fRVEParticleRadius, "Length") << G4endl;
  G4cout << "  nodes:  " << positions.size() << G4endl;
}

void DetectorConstruction::SetGeometryMode(const G4String& mode)
{
  if (mode == "rve_explicit") {
    fGeometryMode = GeometryMode::RVEParameterised;
  } else if (mode == "rve_multiunion") {
    fGeometryMode = GeometryMode::RVEMultiUnion;
  } else {
    fGeometryMode = GeometryMode::Slab;
  }
  if (G4RunManager::GetRunManager()) {
    G4RunManager::GetRunManager()->ReinitializeGeometry();
  }
}

void DetectorConstruction::SetRVEMatrixMaterial(const G4String& name)
{
  fRVEMatrixMaterialName = name;
}
void DetectorConstruction::SetRVEFillerMaterial(const G4String& name)
{
  fRVEFillerMaterialName = name;
}
void DetectorConstruction::SetRVESideLength(G4double length)
{
  fRVESideLength = length;
}
void DetectorConstruction::SetRVEParticleRadius(G4double radius)
{
  fRVEParticleRadius = radius;
}
void DetectorConstruction::SetRVEVolumeFraction(G4double phi)
{
  fRVEVolumeFraction = phi;
}
void DetectorConstruction::SetRVEMaxParticles(G4int n)
{
  fRVEMaxParticles = n;
}
void DetectorConstruction::SetRVESeed(G4int seed)
{
  fRVESeed = static_cast<G4long>(seed);
}

void DetectorConstruction::ConstructSDandField()
{
  // In RVE mode there are no ShieldLayer logical volumes; skip SD registration.
  if (fGeometryMode != GeometryMode::Slab) return;

  // Phase 1: per-layer G4MultiFunctionalDetector with energy-deposit and
  // dose-deposit primitive scorers.  One SD per layer; all segment logical
  // volumes belonging to that layer share the same SD so totals are merged
  // automatically by Geant4 via the copy-number keyed hits map.
  G4SDManager* sdm = G4SDManager::GetSDMpointer();

  for (std::size_t layerIdx = 0; layerIdx < fLayers.size(); ++layerIdx) {
    const G4String sdName = "ShieldLayerSD_" + std::to_string(layerIdx);

    // Avoid re-registration on geometry reinit.
    if (sdm->FindSensitiveDetector(sdName, false)) {
      continue;
    }

    auto* det = new G4MultiFunctionalDetector(sdName);
    det->RegisterPrimitive(new G4PSEnergyDeposit("edep"));
    det->RegisterPrimitive(new G4PSDoseDeposit("dose"));
    sdm->AddNewDetector(det);

    const G4int divisions = std::max(1, fLayers[layerIdx].divisions);
    for (G4int div = 0; div < divisions; ++div) {
      const G4String logName =
        "ShieldLayerLogical_" + std::to_string(layerIdx) + "_" + std::to_string(div);
      SetSensitiveDetector(logName, det);
    }
  }
}

void DetectorConstruction::ClearLayers()
{
  fLayers.clear();
  G4RunManager::GetRunManager()->ReinitializeGeometry();
}

void DetectorConstruction::AddMassFractionMaterialCommand(const G4String& spec)
{
  MaterialRegistry::Instance()->AddMassFractionMaterialCommand(spec);
}

void DetectorConstruction::AddLayerCommand(const G4String& spec)
{
  std::istringstream stream(spec);
  G4String materialName;
  G4double thickness = 0.;
  G4String unit;
  G4int divisions = 1;

  stream >> materialName >> thickness >> unit;
  if (!stream) {
    G4Exception("DetectorConstruction::AddLayerCommand", "ShieldLab001", JustWarning,
                "Expected: material thickness unit [divisions]");
    return;
  }
  stream >> divisions;

  const G4double unitValue = G4UnitDefinition::GetValueOf(unit);
  AddLayer(materialName, thickness * unitValue, divisions);
}

void DetectorConstruction::AddLayer(const G4String& materialName, G4double thickness, G4int divisions)
{
  if (thickness <= DBL_MIN) {
    G4Exception("DetectorConstruction::AddLayer", "ShieldLab002", JustWarning,
                "Layer thickness must be positive.");
    return;
  }
  if (divisions < 1) {
    divisions = 1;
  }
  fLayers.push_back({materialName, thickness, divisions});
  if (G4RunManager::GetRunManager()) {
    G4RunManager::GetRunManager()->ReinitializeGeometry();
  }
}

void DetectorConstruction::SetTransverseSize(G4double size)
{
  if (size > DBL_MIN) {
    fTransverseSize = size;
    G4RunManager::GetRunManager()->ReinitializeGeometry();
  }
}

const std::vector<ShieldLayer>& DetectorConstruction::GetLayers() const
{
  return fLayers;
}

G4double DetectorConstruction::GetTotalThickness() const
{
  G4double total = 0.;
  for (const auto& layer : fLayers) {
    total += layer.thickness;
  }
  return total;
}

G4double DetectorConstruction::GetTransverseSize() const
{
  return fTransverseSize;
}

G4double DetectorConstruction::GetWorldHalfX() const
{
  return fWorldHalfX;
}

G4Material* DetectorConstruction::GetLayerMaterial(G4int index) const
{
  if (index < 0 || static_cast<std::size_t>(index) >= fLayers.size()) {
    return nullptr;
  }
  if (static_cast<std::size_t>(index) >= fLayerMaterials.size()) {
    fLayerMaterials.resize(fLayers.size(), nullptr);
  }
  if (fLayerMaterials[index] == nullptr) {
    fLayerMaterials[index] = ResolveMaterial(fLayers[index].materialName);
  }
  return fLayerMaterials[index];
}

G4int DetectorConstruction::GetLayerIndexForSegment(G4int copyNumber) const
{
  if (copyNumber < 0 || static_cast<std::size_t>(copyNumber) >= fSegmentLayerIndex.size()) {
    return copyNumber;
  }
  return fSegmentLayerIndex[copyNumber];
}

G4Material* DetectorConstruction::ResolveMaterial(const G4String& materialName) const
{
  auto* material = MaterialRegistry::Instance()->FindOrBuildMaterial(materialName);
  if (!material) {
    G4Exception("DetectorConstruction::ResolveMaterial", "ShieldLab003", FatalException,
                ("Unknown material: " + materialName).c_str());
  }
  return material;
}