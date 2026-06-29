#ifndef MaterialRegistry_h
#define MaterialRegistry_h 1

#include "globals.hh"

class G4Material;

class MaterialRegistry
{
  public:
    static MaterialRegistry* Instance();

    void AddMassFractionMaterialCommand(const G4String& spec);
    G4Material* FindOrBuildMaterial(const G4String& materialName) const;

  private:
    MaterialRegistry() = default;
};

#endif