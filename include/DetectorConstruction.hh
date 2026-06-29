#ifndef DetectorConstruction_h
#define DetectorConstruction_h 1

#include "ShieldLayer.hh"

#include "G4ThreeVector.hh"
#include "G4VUserDetectorConstruction.hh"
#include "globals.hh"

#include <vector>

class G4GenericMessenger;
class G4LogicalVolume;
class G4Material;
class G4VPhysicalVolume;
class DetectorMessenger;

class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction();
    ~DetectorConstruction() override;

    G4VPhysicalVolume* Construct() override;
    void ConstructSDandField() override;

    void ClearLayers();
    void AddMassFractionMaterialCommand(const G4String& spec);
    void AddLayerCommand(const G4String& spec);
    void AddLayer(const G4String& materialName, G4double thickness, G4int divisions = 1);
    void SetTransverseSize(G4double size);

    const std::vector<ShieldLayer>& GetLayers() const;
    G4double GetTotalThickness() const;
    G4double GetTransverseSize() const;
    G4double GetWorldHalfX() const;
    G4double GetRVESideLength() const { return fRVESideLength; }
    G4Material* GetLayerMaterial(G4int index) const;
    G4int GetLayerIndexForSegment(G4int copyNumber) const;

    // ── RVE geometry (regimes B and C) ───────────────────────────────────
    void SetGeometryMode(const G4String& mode);
    void SetRVEMatrixMaterial(const G4String& name);
    void SetRVEFillerMaterial(const G4String& name);
    void SetRVESideLength(G4double length);
    void SetRVEParticleRadius(G4double radius);
    void SetRVEVolumeFraction(G4double phi);
    void SetRVEMaxParticles(G4int n);
    void SetRVESeed(G4int seed);

  private:
    void DefineDefaultMaterials();
    G4Material* ResolveMaterial(const G4String& materialName) const;

    // ── Slab state ───────────────────────────────────────────────────────
    std::vector<ShieldLayer> fLayers;
    mutable std::vector<G4Material*> fLayerMaterials;
    std::vector<G4int> fSegmentLayerIndex;
    G4double fTransverseSize = 10.0;
    G4double fWorldPadding   = 2.0;
    G4double fWorldHalfX     = 0.0;
    G4Material* fWorldMaterial = nullptr;
    DetectorMessenger* fMessenger = nullptr;

    // ── Geometry mode ────────────────────────────────────────────────────
    enum class GeometryMode { Slab, RVEParameterised, RVEMultiUnion };
    GeometryMode fGeometryMode = GeometryMode::Slab;

    // ── RVE parameters ───────────────────────────────────────────────────
    G4String fRVEMatrixMaterialName;
    G4String fRVEFillerMaterialName;
    G4double fRVESideLength     = 0.0;
    G4double fRVEParticleRadius = 0.0;
    G4double fRVEVolumeFraction = 0.0;
    G4int    fRVEMaxParticles   = 2000;
    G4long   fRVESeed           = 12345;

    // ── Private build helpers ─────────────────────────────────────────────
    void BuildSlab(G4LogicalVolume* worldLogic);
    void BuildRVEParameterised(G4LogicalVolume* worldLogic);
    void BuildRVEMultiUnion(G4LogicalVolume* worldLogic);
    static std::vector<G4ThreeVector> ComputeRSAPositions(
        G4double sideLength, G4double particleRadius,
        G4double volumeFraction, G4int maxParticles, G4long seed);
};

#endif