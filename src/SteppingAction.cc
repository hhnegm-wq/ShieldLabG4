#include "SteppingAction.hh"

#include "DetectorConstruction.hh"
#include "EventAction.hh"

#include "G4ParticleDefinition.hh"
#include "G4Step.hh"
#include "G4StepPoint.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"
#include "G4VPhysicalVolume.hh"

#include <algorithm>

namespace {

G4bool IsUncollidedPrimaryGamma(const G4Track* track)
{
  if (!track || track->GetTrackID() != 1) {
    return false;
  }
  if (track->GetDefinition()->GetParticleName() != "gamma") {
    return false;
  }

  const G4double vertexEnergy = track->GetVertexKineticEnergy();
  const G4double currentEnergy = track->GetKineticEnergy();
  const G4double energyTolerance = std::max(1.0e-9 * std::max(vertexEnergy, 1.0 * eV), 1.0e-9 * eV);
  const G4double directionCosine = track->GetMomentumDirection().dot(track->GetVertexMomentumDirection());
  return std::abs(currentEnergy - vertexEnergy) <= energyTolerance && directionCosine >= 0.999999;
}

}

SteppingAction::SteppingAction(const DetectorConstruction* detector, EventAction* eventAction)
  : fDetector(detector), fEventAction(eventAction)
{}

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  const auto* track    = step->GetTrack();
  const auto* prePoint = step->GetPreStepPoint();
  const auto* postPoint = step->GetPostStepPoint();

  // ── Layer energy deposition (all tracks contribute to Edep) ──────────────
  const auto* preVolume = prePoint->GetPhysicalVolume();
  if (preVolume && preVolume->GetName() == "ShieldLayer") {
    const G4int layerIndex = fDetector
      ? fDetector->GetLayerIndexForSegment(preVolume->GetCopyNo())
      : preVolume->GetCopyNo();
    fEventAction->AddLayerEnergy(layerIndex, step->GetTotalEnergyDeposit());
  }

  // ── World-boundary crossing check ────────────────────────────────────────
  if (postPoint->GetStepStatus() != fWorldBoundary) {
    return;
  }

  const bool downstream = (postPoint->GetPosition().x() > 0.);

  // Broad-beam buildup transport observable: all downstream photons,
  // with primary-vs-total separation for strict Monte Carlo buildup scoring.
  if (downstream && track->GetDefinition()->GetParticleName() == "gamma") {
    const G4double ke_MeV = track->GetKineticEnergy() / MeV;
    fEventAction->AddDownstreamPhoton(track->GetTrackID() == 1, ke_MeV);
  }

  if (track->GetTrackID() == 1) {
    // Primary particle exiting the geometry
    if (downstream) {
      if (track->GetDefinition()->GetParticleName() != "gamma" || IsUncollidedPrimaryGamma(track)) {
        fEventAction->MarkTransmitted();
      }
    }
    else {
      fEventAction->MarkReflected();
    }
  }
  else {
    // Secondary particle exiting downstream — tally by particle species
    if (downstream) {
      const G4double ke_MeV = track->GetKineticEnergy() / MeV;
      fEventAction->AddSecondary(
        track->GetDefinition()->GetParticleName(),
        ke_MeV
      );
    }
  }
}
