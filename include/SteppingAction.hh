#ifndef SteppingAction_h
#define SteppingAction_h 1

#include "G4UserSteppingAction.hh"

class DetectorConstruction;
class EventAction;
class G4Step;

class SteppingAction : public G4UserSteppingAction
{
  public:
    SteppingAction(const DetectorConstruction* detector, EventAction* eventAction);

    void UserSteppingAction(const G4Step* step) override;

  private:
    const DetectorConstruction* fDetector = nullptr;
    EventAction* fEventAction = nullptr;
};

#endif