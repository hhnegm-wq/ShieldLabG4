#ifndef EventAction_h
#define EventAction_h 1

#include "G4UserEventAction.hh"
#include "globals.hh"

#include <map>
#include <vector>

class DetectorConstruction;
class RunAction;
class G4Event;

class EventAction : public G4UserEventAction
{
  public:
    EventAction(const DetectorConstruction* detector, RunAction* runAction);

    void BeginOfEventAction(const G4Event* event) override;
    void EndOfEventAction(const G4Event* event) override;

    void AddLayerEnergy(G4int layerIndex, G4double energy);
    void MarkTransmitted();
    void MarkReflected();
    void AddDownstreamPhoton(G4bool isPrimary, G4double kineticEnergy_MeV);

    // Secondary particle tally — called by SteppingAction when a secondary
    // exits the downstream face of the shield (x > 0 world boundary).
    void AddSecondary(const G4String& particleName, G4double kineticEnergy_MeV);

  private:
    const DetectorConstruction* fDetector = nullptr;
    RunAction* fRunAction = nullptr;
    std::vector<G4double> fLayerEdep;
    G4bool fTransmitted = false;
    G4bool fReflected = false;

    // Per-event downstream secondary energy samples by particle species.
    std::map<G4String, std::vector<G4double>> fSecondaryEnergySamplesMeV;

    // Per-event downstream photon transport samples for buildup and spectrum export.
    std::vector<G4double> fPrimaryDownstreamPhotonEnergiesMeV;
    std::vector<G4double> fTotalDownstreamPhotonEnergiesMeV;
};

#endif
