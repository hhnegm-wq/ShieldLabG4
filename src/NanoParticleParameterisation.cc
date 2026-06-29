#include "NanoParticleParameterisation.hh"

#include "G4VPhysicalVolume.hh"

NanoParticleParameterisation::NanoParticleParameterisation(
    std::vector<G4ThreeVector> positions)
  : fPositions(std::move(positions))
{}

void NanoParticleParameterisation::ComputeTransformation(G4int copyNumber,
                                                          G4VPhysicalVolume* physVol) const
{
  physVol->SetTranslation(fPositions[static_cast<std::size_t>(copyNumber)]);
  physVol->SetRotation(nullptr);
}
