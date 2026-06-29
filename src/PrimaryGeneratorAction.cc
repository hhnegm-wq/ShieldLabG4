#include "PrimaryGeneratorAction.hh"

#include "DetectorConstruction.hh"

#include "G4Event.hh"
#include "G4Gamma.hh"
#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

PrimaryGeneratorAction::PrimaryGeneratorAction(const DetectorConstruction* detector) : fDetector(detector)
{
  fParticleGun = new G4ParticleGun(1);
  fParticleGun->SetParticleDefinition(G4Gamma::GammaDefinition());
  fParticleGun->SetParticleEnergy(662.0 * keV);
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(1., 0., 0.));
}

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  const G4double startX = -fDetector->GetWorldHalfX() + 1.0 * mm;

  // For explicit-RVE geometries (regimes B and C), distribute the beam
  // uniformly over the full transverse cross-section of the RVE box.
  // A pencil beam at (0,0) is non-ergodic for small N: with N=45 spheres
  // the single path may sample very different phi than the bulk average.
  // Uniform sampling over Y-Z converges to the population-averaged MAC
  // regardless of N, making the measurement geometry-representation-independent.
  G4double startY = 0.0;
  G4double startZ = 0.0;
  const G4double rveSide = fDetector ? fDetector->GetRVESideLength() : 0.0;
  if (rveSide > 0.0) {
    startY = (G4UniformRand() - 0.5) * rveSide;
    startZ = (G4UniformRand() - 0.5) * rveSide;
  }

  fParticleGun->SetParticlePosition(G4ThreeVector(startX, startY, startZ));
  fParticleGun->GeneratePrimaryVertex(event);
}