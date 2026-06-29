#ifndef NanoParticleParameterisation_h
#define NanoParticleParameterisation_h 1

#include "G4VPVParameterisation.hh"
#include "G4ThreeVector.hh"

#include <vector>

class G4VPhysicalVolume;

/// @brief Parameterised placement for explicit nanoparticle geometry (Paper 3 regime B).
///
/// Pre-computed RSA sphere centres are stored and applied via G4PVParameterised.
/// Only the translation changes per copy; all copies share the same sphere radius
/// and orientation (identity rotation).
class NanoParticleParameterisation : public G4VPVParameterisation
{
  public:
    explicit NanoParticleParameterisation(std::vector<G4ThreeVector> positions);
    ~NanoParticleParameterisation() override = default;

    void ComputeTransformation(G4int copyNumber, G4VPhysicalVolume* physVol) const override;

    G4int GetNParticles() const { return static_cast<G4int>(fPositions.size()); }

  private:
    std::vector<G4ThreeVector> fPositions;
};

#endif
