#ifndef RunAction_h
#define RunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"

#include <map>
#include <vector>

class DetectorConstruction;
class G4GenericMessenger;
class G4Run;

class RunAction : public G4UserRunAction
{
  public:
    explicit RunAction(const DetectorConstruction* detector);
    ~RunAction() override;

    void BeginOfRunAction(const G4Run* run) override;
    void EndOfRunAction(const G4Run* run) override;

    void AccumulateEvent(const std::vector<G4double>& layerEdep, G4bool transmitted, G4bool reflected);

    // Accumulate per-layer dose and energy-deposit from G4PSDoseDeposit /
    // G4PSEnergyDeposit sensitive-detector scorers (Phase 1).
    // doseGy: absorbed dose in Gy (G4PSDoseDeposit units).
    // edepMeV: total energy deposit in MeV (G4PSEnergyDeposit / MeV).
    void AccumulateLayerDose(G4int layerIdx, G4double doseGy, G4double edepMeV);

    // Accumulate one secondary particle reaching the downstream boundary.
    // particleName: G4 particle name (e.g. "gamma", "e-", "proton").
    // kineticEnergy_MeV: kinetic energy at the moment of crossing the boundary.
    void AccumulateSecondary(const G4String& particleName, G4double kineticEnergy_MeV);
    void AccumulateDownstreamPhoton(
      G4int primaryCount,
      G4int totalCount,
      G4double primaryEnergyMeV,
      G4double totalEnergyMeV
    );
    void AccumulateDownstreamPhotonSample(G4bool isPrimary, G4double kineticEnergy_MeV);

    void SetOutputDirectory(const G4String& value);

  private:
    void BuildCommands();
    void EnsureOutputDirectory() const;

    const DetectorConstruction* fDetector = nullptr;
    G4GenericMessenger* fMessenger = nullptr;
    G4String fOutputDirectory = "results";

    // Primary-particle accumulators
    std::vector<G4double> fLayerEdep;
    G4int fEvents = 0;
    G4int fTransmitted = 0;
    G4int fReflected = 0;

    // Secondary-particle accumulators: particle name → (count, total KE in MeV)
    std::map<G4String, G4int>    fSecondaryCount;
    std::map<G4String, G4double> fSecondaryEnergy;

    // Broad-beam photon transport accumulators at the downstream boundary.
    G4int fPrimaryDownstreamPhotonCount = 0;
    G4int fTotalDownstreamPhotonCount = 0;
    G4double fPrimaryDownstreamPhotonEnergyMeV = 0.0;
    G4double fTotalDownstreamPhotonEnergyMeV = 0.0;
    std::vector<G4int> fPrimaryDownstreamPhotonSpectrum;
    std::vector<G4int> fTotalDownstreamPhotonSpectrum;
    std::map<G4String, std::vector<G4int>> fSecondarySpectrum;

    // Phase 1: batch-means uncertainty (transmission). Batch size is set in
    // AccumulateEvent so that a run yields ~10 equal-size batches.
    std::vector<G4int> fBatchTransmitted;
    std::vector<G4int> fBatchEvents;
    G4int fCurrentBatchTransmitted = 0;
    G4int fCurrentBatchEvents = 0;

    // Phase 1: per-layer absorbed dose and energy-deposit from SD scorers.
    std::vector<G4double> fLayerDoseGy;
    std::vector<G4double> fLayerEdepSD;
};

#endif
