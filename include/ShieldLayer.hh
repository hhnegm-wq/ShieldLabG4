#ifndef ShieldLayer_h
#define ShieldLayer_h 1

#include "globals.hh"

struct ShieldLayer
{
  G4String materialName;
  G4double thickness = 0.;
  G4int divisions = 1;
};

#endif