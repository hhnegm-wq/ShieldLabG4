#ifndef DetectorMessenger_h
#define DetectorMessenger_h 1

#include "G4UImessenger.hh"
#include "globals.hh"

class DetectorConstruction;
class G4UIdirectory;
class G4UIcmdWithoutParameter;
class G4UIcmdWithAString;
class G4UIcmdWithADouble;
class G4UIcmdWithADoubleAndUnit;
class G4UIcmdWithAnInteger;
class G4UIcommand;

class DetectorMessenger : public G4UImessenger
{
  public:
    explicit DetectorMessenger(DetectorConstruction* detector);
    ~DetectorMessenger() override;

    void SetNewValue(G4UIcommand* command, G4String value) override;

  private:
    DetectorConstruction* fDetector = nullptr;
    G4UIdirectory* fGeometryDirectory = nullptr;
    G4UIdirectory* fMaterialDirectory = nullptr;
    G4UIdirectory* fRVEDirectory = nullptr;
    G4UIcmdWithAString* fAddMassFractionMaterialCommand = nullptr;
    G4UIcmdWithoutParameter* fClearLayersCommand = nullptr;
    G4UIcmdWithAString* fAddLayerCommand = nullptr;
    G4UIcmdWithADoubleAndUnit* fTransverseSizeCommand = nullptr;
    // RVE commands
    G4UIcmdWithAString*    fGeometryModeCommand = nullptr;
    G4UIcmdWithAString*    fRVEMatrixMaterialCommand = nullptr;
    G4UIcmdWithAString*    fRVEFillerMaterialCommand = nullptr;
    G4UIcmdWithADoubleAndUnit* fRVESideLengthCommand = nullptr;
    G4UIcmdWithADoubleAndUnit* fRVEParticleRadiusCommand = nullptr;
    G4UIcmdWithADouble*    fRVEVolumeFractionCommand = nullptr;
    G4UIcmdWithAnInteger*  fRVEMaxParticlesCommand = nullptr;
    G4UIcmdWithAnInteger*  fRVESeedCommand = nullptr;
};

#endif