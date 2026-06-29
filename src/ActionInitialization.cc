#include "ActionInitialization.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "SteppingAction.hh"

ActionInitialization::ActionInitialization(const DetectorConstruction* detector) : fDetector(detector) {}

void ActionInitialization::Build() const
{
  SetUserAction(new PrimaryGeneratorAction(fDetector));
  auto* runAction = new RunAction(fDetector);
  SetUserAction(runAction);
  auto* eventAction = new EventAction(fDetector, runAction);
  SetUserAction(eventAction);
  SetUserAction(new SteppingAction(fDetector, eventAction));
}