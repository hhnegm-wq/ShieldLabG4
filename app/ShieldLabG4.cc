#include "ActionInitialization.hh"
#include "DetectorConstruction.hh"

#include "G4PhysListFactory.hh"
#include "G4DecayPhysics.hh"
#include "G4EmLivermorePhysics.hh"
#include "G4EmParameters.hh"
#include "G4EmStandardPhysics_option4.hh"
#include "G4RunManagerFactory.hh"
#include "G4SteppingVerbose.hh"
#include "G4UIExecutive.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4VModularPhysicsList.hh"
#include "G4ios.hh"
#include "Randomize.hh"

#include <chrono>
#include <cstdlib>
#include <cstring>
#include <string>

namespace {

G4RunManagerType ResolveRunManagerType()
{
  const char* rawMode = std::getenv("SHIELDLAB_RUN_MANAGER");
  if (!rawMode) {
    return G4RunManagerType::Serial;
  }

  std::string mode(rawMode);
  for (char& ch : mode) {
    ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
  }

  if (mode == "default" || mode == "auto") {
    return G4RunManagerType::Default;
  }

#ifdef G4MULTITHREADED
  if (mode == "mt" || mode == "multithreaded") {
    return G4RunManagerType::MT;
  }
#else
  if (mode == "mt" || mode == "multithreaded") {
    G4cout << "SHIELDLAB_RUN_MANAGER requested MT, but this Geant4 build does not support it. Falling back to serial." << G4endl;
  }
#endif

  return G4RunManagerType::Serial;
}

G4VModularPhysicsList* BuildDefaultPhysicsList()
{
  auto* physicsList = new G4VModularPhysicsList();
  physicsList->SetVerboseLevel(0);
  physicsList->RegisterPhysics(new G4EmStandardPhysics_option4(0));
  physicsList->RegisterPhysics(new G4DecayPhysics(0));
  return physicsList;
}

G4VModularPhysicsList* BuildPhysicsList(const char* rawPhysics)
{
  if (!rawPhysics || std::strlen(rawPhysics) == 0) {
    return BuildDefaultPhysicsList();
  }

  std::string physics(rawPhysics);
  std::string key = physics;
  for (char& ch : key) {
    ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
  }

  auto* physicsList = new G4VModularPhysicsList();
  physicsList->SetVerboseLevel(0);
  if (key == "emlivermore" || key == "g4emlivermorephysics") {
    physicsList->RegisterPhysics(new G4EmLivermorePhysics(0));
    physicsList->RegisterPhysics(new G4DecayPhysics(0));
    return physicsList;
  }
  if (key == "emstandard_opt4" || key == "g4emstandardphysics_option4" || key == "emstandardoption4") {
    physicsList->RegisterPhysics(new G4EmStandardPhysics_option4(0));
    physicsList->RegisterPhysics(new G4DecayPhysics(0));
    return physicsList;
  }
  delete physicsList;

  G4PhysListFactory physicsFactory;
  if (auto* referencePhysics = physicsFactory.GetReferencePhysList(physics)) {
    return referencePhysics;
  }

  G4cout << "Unknown SHIELDLAB_PHYSICS_LIST='" << physics
         << "'. Falling back to G4EmStandardPhysics_option4+G4DecayPhysics." << G4endl;
  return BuildDefaultPhysicsList();
}

// Phase 0 hardening: explicit, persisted seed for reproducibility.
// Resolution order: --seed=<N> CLI arg -> SHIELDLAB_SEED env -> wall-clock.
// The chosen seed is exported back into SHIELDLAB_SEED so RunAction can record
// it in run_summary.csv.
long ResolveSeed(int& argc, char** argv)
{
  long seed = 0;
  bool found = false;
  for (int i = 1; i < argc; ++i) {
    if (std::strncmp(argv[i], "--seed=", 7) == 0) {
      seed = std::atol(argv[i] + 7);
      found = true;
      // Strip the flag so Geant4's argument handling is unaffected.
      for (int j = i; j < argc - 1; ++j) argv[j] = argv[j + 1];
      --argc;
      break;
    }
  }
  if (!found) {
    if (const char* env = std::getenv("SHIELDLAB_SEED")) {
      seed = std::atol(env);
      found = seed != 0;
    }
  }
  if (!found || seed == 0) {
    using namespace std::chrono;
    seed = static_cast<long>(
      duration_cast<nanoseconds>(steady_clock::now().time_since_epoch()).count() & 0x7fffffffL);
  }
#ifdef _WIN32
  _putenv_s("SHIELDLAB_SEED", std::to_string(seed).c_str());
#else
  setenv("SHIELDLAB_SEED", std::to_string(seed).c_str(), 1);
#endif
  return seed;
}

}  // namespace

int main(int argc, char** argv)
{
  G4UIExecutive* ui = nullptr;
  if (argc == 1) {
    ui = new G4UIExecutive(argc, argv);
  }

  const long seed = ResolveSeed(argc, argv);
  G4Random::setTheEngine(new CLHEP::RanecuEngine);
  G4Random::setTheSeed(seed);
  G4cout << "[ShieldLabG4] RNG=RanecuEngine seed=" << seed << G4endl;
  G4SteppingVerbose::UseBestUnit(4);

  auto* runManager = G4RunManagerFactory::CreateRunManager(ResolveRunManagerType());

  auto* detector = new DetectorConstruction();
  runManager->SetUserInitialization(detector);

  G4EmParameters::Instance()->SetVerbose(0);
  runManager->SetUserInitialization(BuildPhysicsList(std::getenv("SHIELDLAB_PHYSICS_LIST")));
  runManager->SetUserInitialization(new ActionInitialization(detector));

  G4VisManager* visManager = nullptr;
  auto* uiManager = G4UImanager::GetUIpointer();

  if (ui) {
    visManager = new G4VisExecutive();
    visManager->Initialize();
    ui->SessionStart();
    delete ui;
  }
  else {
    G4String command = "/control/execute ";
    uiManager->ApplyCommand(command + argv[1]);
  }

  delete visManager;
  delete runManager;
  return 0;
}