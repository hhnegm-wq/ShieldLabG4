#include "EventAction.hh"

#include "DetectorConstruction.hh"
#include "RunAction.hh"

#include "G4Event.hh"
#include "G4HCofThisEvent.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4THitsMap.hh"

EventAction::EventAction(const DetectorConstruction* detector, RunAction* runAction)
  : fDetector(detector), fRunAction(runAction)
{}

void EventAction::BeginOfEventAction(const G4Event*)
{
  fLayerEdep.assign(fDetector->GetLayers().size(), 0.);
  fTransmitted = false;
  fReflected = false;
  fSecondaryEnergySamplesMeV.clear();
  fPrimaryDownstreamPhotonEnergiesMeV.clear();
  fTotalDownstreamPhotonEnergiesMeV.clear();
}

void EventAction::EndOfEventAction(const G4Event* event)
{
  // Phase 1: read per-layer dose and energy-deposit from SD hits collections.
  G4HCofThisEvent* hce = event->GetHCofThisEvent();
  if (hce) {
    auto* sdm = G4SDManager::GetSDMpointer();
    for (std::size_t layerIdx = 0; layerIdx < fDetector->GetLayers().size(); ++layerIdx) {
      const G4String sdName = "ShieldLayerSD_" + std::to_string(layerIdx);

      G4double doseGy  = 0.;
      const G4int doseColId = sdm->GetCollectionID(sdName + "/dose");
      if (doseColId >= 0) {
        const auto* doseMap =
          static_cast<const G4THitsMap<G4double>*>(hce->GetHC(doseColId));
        if (doseMap) {
          for (const auto& kv : *doseMap->GetMap()) {
            doseGy += *(kv.second);
          }
        }
      }

      G4double edepMeV = 0.;
      const G4int edepColId = sdm->GetCollectionID(sdName + "/edep");
      if (edepColId >= 0) {
        const auto* edepMap =
          static_cast<const G4THitsMap<G4double>*>(hce->GetHC(edepColId));
        if (edepMap) {
          for (const auto& kv : *edepMap->GetMap()) {
            edepMeV += *(kv.second) / MeV;
          }
        }
      }

      fRunAction->AccumulateLayerDose(static_cast<G4int>(layerIdx), doseGy, edepMeV);
    }
  }

  G4int primaryDownstreamPhotonCount = 0;
  G4int totalDownstreamPhotonCount = 0;
  G4double primaryDownstreamPhotonEnergyMeV = 0.0;
  G4double totalDownstreamPhotonEnergyMeV = 0.0;
  for (const auto& energy : fPrimaryDownstreamPhotonEnergiesMeV) {
    ++primaryDownstreamPhotonCount;
    primaryDownstreamPhotonEnergyMeV += energy;
    fRunAction->AccumulateDownstreamPhotonSample(true, energy);
  }
  for (const auto& energy : fTotalDownstreamPhotonEnergiesMeV) {
    ++totalDownstreamPhotonCount;
    totalDownstreamPhotonEnergyMeV += energy;
    fRunAction->AccumulateDownstreamPhotonSample(false, energy);
  }

  fRunAction->AccumulateEvent(fLayerEdep, fTransmitted, fReflected);
  fRunAction->AccumulateDownstreamPhoton(
    primaryDownstreamPhotonCount,
    totalDownstreamPhotonCount,
    primaryDownstreamPhotonEnergyMeV,
    totalDownstreamPhotonEnergyMeV
  );

  // Forward exact downstream secondary energy samples to the run accumulator.
  for (const auto& [name, energies] : fSecondaryEnergySamplesMeV) {
    for (const auto& energy : energies) {
      fRunAction->AccumulateSecondary(name, energy);
    }
  }
}

void EventAction::AddLayerEnergy(G4int layerIndex, G4double energy)
{
  if (layerIndex < 0) {
    return;
  }
  const auto index = static_cast<std::size_t>(layerIndex);
  if (index >= fLayerEdep.size()) {
    return;
  }
  fLayerEdep[index] += energy;
}

void EventAction::MarkTransmitted()
{
  fTransmitted = true;
}

void EventAction::MarkReflected()
{
  fReflected = true;
}

void EventAction::AddSecondary(const G4String& particleName, G4double kineticEnergy_MeV)
{
  fSecondaryEnergySamplesMeV[particleName].push_back(kineticEnergy_MeV);
}

void EventAction::AddDownstreamPhoton(G4bool isPrimary, G4double kineticEnergy_MeV)
{
  fTotalDownstreamPhotonEnergiesMeV.push_back(kineticEnergy_MeV);
  if (isPrimary) {
    fPrimaryDownstreamPhotonEnergiesMeV.push_back(kineticEnergy_MeV);
  }
}
