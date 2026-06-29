#include "RunAction.hh"

#include "DetectorConstruction.hh"

#include "G4GenericMessenger.hh"
#include "G4Material.hh"
#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "G4ios.hh"

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>

namespace {

constexpr G4int kSpectrumBinCount = 64;
constexpr G4double kSpectrumMinEnergyMeV = 1.0e-3;
constexpr G4double kSpectrumMaxEnergyMeV = 15.0;

G4int SpectrumBinIndex(G4double energyMeV)
{
  if (energyMeV <= 0.0) {
    return -1;
  }
  const G4double clamped = std::min(std::max(energyMeV, kSpectrumMinEnergyMeV), kSpectrumMaxEnergyMeV);
  const G4double logMin = std::log10(kSpectrumMinEnergyMeV);
  const G4double logMax = std::log10(kSpectrumMaxEnergyMeV);
  const G4double fraction = (std::log10(clamped) - logMin) / (logMax - logMin);
  const G4int index = static_cast<G4int>(fraction * kSpectrumBinCount);
  return std::min(std::max(index, 0), kSpectrumBinCount - 1);
}

G4double SpectrumBinLowerEdge(G4int index)
{
  const G4double logMin = std::log10(kSpectrumMinEnergyMeV);
  const G4double logMax = std::log10(kSpectrumMaxEnergyMeV);
  const G4double fraction = static_cast<G4double>(index) / kSpectrumBinCount;
  return std::pow(10.0, logMin + (logMax - logMin) * fraction);
}

G4double SpectrumBinUpperEdge(G4int index)
{
  return SpectrumBinLowerEdge(index + 1);
}

}

RunAction::RunAction(const DetectorConstruction* detector) : fDetector(detector)
{
  BuildCommands();
}

RunAction::~RunAction()
{
  delete fMessenger;
}

void RunAction::BuildCommands()
{
  fMessenger = new G4GenericMessenger(this, "/shield/output/", "Shield output controls");
  auto& output = fMessenger->DeclareMethod("setDirectory", &RunAction::SetOutputDirectory,
                                           "Set output directory for CSV result files.");
  output.SetParameterName("directory", false);
}

void RunAction::BeginOfRunAction(const G4Run*)
{
  fEvents = 0;
  fTransmitted = 0;
  fReflected = 0;
  fLayerEdep.assign(fDetector->GetLayers().size(), 0.);
  fSecondaryCount.clear();
  fSecondaryEnergy.clear();
  fPrimaryDownstreamPhotonCount = 0;
  fTotalDownstreamPhotonCount = 0;
  fPrimaryDownstreamPhotonEnergyMeV = 0.0;
  fTotalDownstreamPhotonEnergyMeV = 0.0;
  fPrimaryDownstreamPhotonSpectrum.assign(kSpectrumBinCount, 0);
  fTotalDownstreamPhotonSpectrum.assign(kSpectrumBinCount, 0);
  fSecondarySpectrum.clear();
  fBatchTransmitted.clear();
  fBatchEvents.clear();
  fCurrentBatchTransmitted = 0;
  fCurrentBatchEvents = 0;
  fLayerDoseGy.assign(fDetector->GetLayers().size(), 0.);
  fLayerEdepSD.assign(fDetector->GetLayers().size(), 0.);
  EnsureOutputDirectory();
}

void RunAction::EndOfRunAction(const G4Run*)
{
  EnsureOutputDirectory();
  const G4double totalThicknessCm = fDetector->GetTotalThickness() / cm;
  const G4double transmission = fEvents > 0 ? static_cast<G4double>(fTransmitted) / fEvents : 0.;
  const G4double reflection = fEvents > 0 ? static_cast<G4double>(fReflected) / fEvents : 0.;
  const G4double absorption = 1.0 - transmission - reflection;
  G4double muPerCm = 0.;
  const G4String transportCountBasis = "uncollided_primary_gamma_world_boundary";
  const G4String attenuationModel = "beer_lambert_uncollided_primary_transmission";
  G4String attenuationEstimateType = "not_computed";
  if (transmission > 0. && totalThicknessCm > 0.) {
    muPerCm = -std::log(transmission) / totalThicknessCm;
    attenuationEstimateType = "direct";
  }
  else if (fEvents > 0 && totalThicknessCm > 0.) {
    muPerCm = -std::log(0.5 / fEvents) / totalThicknessCm;
    attenuationEstimateType = "lower_bound_zero_transmission";
  }

  // Phase 1: batch-means statistical uncertainty on transmission.
  // Final partial batch is flushed if non-empty.
  if (fCurrentBatchEvents > 0) {
    fBatchTransmitted.push_back(fCurrentBatchTransmitted);
    fBatchEvents.push_back(fCurrentBatchEvents);
  }
  G4double transmissionSigma = 0.0;
  G4int batchCount = static_cast<G4int>(fBatchTransmitted.size());
  if (batchCount >= 2) {
    G4double mean = 0.0;
    for (std::size_t i = 0; i < fBatchTransmitted.size(); ++i) {
      const G4double n = static_cast<G4double>(fBatchEvents[i]);
      if (n > 0) mean += static_cast<G4double>(fBatchTransmitted[i]) / n;
    }
    mean /= batchCount;
    G4double var = 0.0;
    for (std::size_t i = 0; i < fBatchTransmitted.size(); ++i) {
      const G4double n = static_cast<G4double>(fBatchEvents[i]);
      const G4double tr = n > 0 ? static_cast<G4double>(fBatchTransmitted[i]) / n : 0.0;
      var += (tr - mean) * (tr - mean);
    }
    var /= (batchCount - 1);  // unbiased
    transmissionSigma = std::sqrt(var / batchCount);  // sigma of the mean
  }

  // Phase 0 hardening: persist seed / RNG / build provenance for reproducibility.
  const char* seedEnv = std::getenv("SHIELDLAB_SEED");
  const G4String seedStr = seedEnv ? seedEnv : "unknown";
  const char* runMgrEnv = std::getenv("SHIELDLAB_RUN_MANAGER");
  const G4String runMgrStr = runMgrEnv ? runMgrEnv : "serial";
  const char* physicsEnv = std::getenv("SHIELDLAB_PHYSICS_LIST");
  const G4String physicsStr = physicsEnv ? physicsEnv : "G4EmStandardPhysics_option4+G4DecayPhysics";

  const auto outputPath = std::filesystem::path(fOutputDirectory.data());

  // ── run_summary.csv ─────────────────────────────────────────────
  std::ofstream summary((outputPath / "run_summary.csv").string());
  summary << "events,transmitted,reflected,transmission_fraction,transmission_sigma,batches,"
             "reflection_fraction,absorption_fraction,total_thickness_cm,"
             "linear_attenuation_cm_inv,attenuation_estimate_type,transport_count_basis,"
             "attenuation_model,seed,rng_engine,run_manager,physics_list\n";
  summary << fEvents << ',' << fTransmitted << ',' << fReflected << ',' << transmission << ','
          << transmissionSigma << ',' << batchCount << ','
          << reflection << ',' << absorption << ',' << totalThicknessCm << ',' << muPerCm << ','
          << attenuationEstimateType << ',' << transportCountBasis << ',' << attenuationModel << ','
          << seedStr << ',' << "RanecuEngine" << ',' << runMgrStr << ',' << physicsStr << '\n';

  // ── layer_energy_deposition.csv ───────────────────────────────────────────
  std::ofstream layers((outputPath / "layer_energy_deposition.csv").string());
  layers << "layer,material,thickness_cm,density_g_cm3,edep_MeV_total,edep_MeV_per_event\n";
  for (std::size_t index = 0; index < fDetector->GetLayers().size(); ++index) {
    const auto& layer = fDetector->GetLayers()[index];
    const auto* material = fDetector->GetLayerMaterial(static_cast<G4int>(index));
    const G4double edepMeV = fLayerEdep[index] / MeV;
    layers << index + 1 << ',' << layer.materialName << ',' << layer.thickness / cm << ','
           << (material ? material->GetDensity() / (g / cm3) : 0.) << ',' << edepMeV << ','
           << (fEvents > 0 ? edepMeV / fEvents : 0.) << '\n';
  }

  // ── layer_dose.csv (Phase 1 SD scorers) ──────────────────────────────────
  // Reports absorbed dose per layer from G4PSDoseDeposit. Dose is in Gy;
  // energy deposit column cross-checks against layer_energy_deposition.csv
  // (which is scored via SteppingAction rather than a sensitive detector).
  std::ofstream doseCsv((outputPath / "layer_dose.csv").string());
  doseCsv << "layer,material,thickness_cm,density_g_cm3,"
             "dose_Gy_total,dose_Gy_per_event,"
             "edep_MeV_sd_total,edep_MeV_sd_per_event\n";
  for (std::size_t idx = 0; idx < fDetector->GetLayers().size(); ++idx) {
    const auto& layer = fDetector->GetLayers()[idx];
    const auto* mat   = fDetector->GetLayerMaterial(static_cast<G4int>(idx));
    const G4double doseTotal = (idx < fLayerDoseGy.size()) ? fLayerDoseGy[idx] : 0.;
    const G4double edepSD    = (idx < fLayerEdepSD.size()) ? fLayerEdepSD[idx] : 0.;
    doseCsv << idx + 1 << ',' << layer.materialName << ','
            << layer.thickness / cm << ','
            << (mat ? mat->GetDensity() / (g / cm3) : 0.) << ','
            << std::setprecision(9) << doseTotal << ','
            << (fEvents > 0 ? doseTotal / fEvents : 0.) << ','
            << edepSD << ','
            << (fEvents > 0 ? edepSD / fEvents : 0.) << '\n';
  }

  // ── secondary_tally.csv ───────────────────────────────────────────────────
  // Records all secondary particles that exited the downstream face of the
  // shield, aggregated over the full run. Useful for assessing bremsstrahlung
  // build-up, activated product radiation, scattered radiation fields, and
  // secondary shielding requirements.
  std::ofstream secondaries((outputPath / "secondary_tally.csv").string());
  secondaries << "particle_name,count,total_kinetic_energy_MeV,mean_kinetic_energy_MeV,"
                 "count_per_primary_event,fraction_of_events_with_secondary\n";

  // Sort entries by count (descending) for readability
  std::vector<std::pair<G4String, G4int>> sorted(fSecondaryCount.begin(), fSecondaryCount.end());
  std::sort(sorted.begin(), sorted.end(),
            [](const auto& a, const auto& b) { return a.second > b.second; });

  for (const auto& [name, count] : sorted) {
    const G4double totalKE  = fSecondaryEnergy.count(name) ? fSecondaryEnergy.at(name) : 0.0;
    const G4double meanKE   = count > 0 ? totalKE / count : 0.0;
    const G4double perEvent = fEvents > 0 ? static_cast<G4double>(count) / fEvents : 0.0;
    // fraction_of_events: approximate — secondary could appear multiple times per event
    const G4double fracEvents = fEvents > 0 ? std::min(perEvent, 1.0) : 0.0;
    secondaries << name << ',' << count << ',' << std::fixed << std::setprecision(6)
                << totalKE << ',' << meanKE << ',' << perEvent << ',' << fracEvents << '\n';
  }

  // ── lcns5_buildup_observable.csv ─────────────────────────────────────────
  // Dedicated strict broad-beam Monte Carlo buildup scoring at downstream
  // boundary based on photon transport (primary vs total including scattered).
  G4int totalSecondaryCount = 0;
  G4double totalSecondaryEnergyMeV = 0.0;
  for (const auto& [name, count] : fSecondaryCount) {
    totalSecondaryCount += count;
    totalSecondaryEnergyMeV += fSecondaryEnergy.count(name) ? fSecondaryEnergy.at(name) : 0.0;
  }
  const G4double countPerPrimaryEvent = fEvents > 0 ? static_cast<G4double>(totalSecondaryCount) / fEvents : 0.0;
  const G4double energyPerPrimaryEvent = fEvents > 0 ? totalSecondaryEnergyMeV / fEvents : 0.0;
  const G4double broadbeamBuildupCount =
    fPrimaryDownstreamPhotonCount > 0
      ? static_cast<G4double>(fTotalDownstreamPhotonCount) / fPrimaryDownstreamPhotonCount
      : std::numeric_limits<G4double>::quiet_NaN();
  const G4double broadbeamBuildupEnergy =
    fPrimaryDownstreamPhotonEnergyMeV > 0.0
      ? fTotalDownstreamPhotonEnergyMeV / fPrimaryDownstreamPhotonEnergyMeV
      : std::numeric_limits<G4double>::quiet_NaN();

  std::ofstream buildup((outputPath / "lcns5_buildup_observable.csv").string());
  buildup << "events,secondary_total_count,secondary_total_kinetic_energy_MeV,"
             "secondary_count_per_primary_event,secondary_energy_per_primary_event_MeV,"
             "primary_downstream_photon_count,total_downstream_photon_count,"
             "primary_downstream_photon_energy_MeV,total_downstream_photon_energy_MeV,"
             "mc_buildup_observable_count,mc_buildup_observable_energy\n";
  buildup << fEvents << ',' << totalSecondaryCount << ',' << std::fixed << std::setprecision(6)
          << totalSecondaryEnergyMeV << ',' << countPerPrimaryEvent << ',' << energyPerPrimaryEvent
          << ',' << fPrimaryDownstreamPhotonCount << ',' << fTotalDownstreamPhotonCount
          << ',' << fPrimaryDownstreamPhotonEnergyMeV << ',' << fTotalDownstreamPhotonEnergyMeV
          << ',' << broadbeamBuildupCount << ',' << broadbeamBuildupEnergy << '\n';

  // ── downstream_spectrum.csv ─────────────────────────────────────────────
  std::ofstream spectrum((outputPath / "downstream_spectrum.csv").string());
  spectrum << "channel,particle_name,bin_index,energy_low_MeV,energy_high_MeV,count\n";
  for (G4int index = 0; index < kSpectrumBinCount; ++index) {
    spectrum << "primary_gamma,gamma," << index << ','
             << SpectrumBinLowerEdge(index) << ',' << SpectrumBinUpperEdge(index) << ','
             << fPrimaryDownstreamPhotonSpectrum[static_cast<std::size_t>(index)] << '\n';
  }
  for (G4int index = 0; index < kSpectrumBinCount; ++index) {
    spectrum << "total_gamma,gamma," << index << ','
             << SpectrumBinLowerEdge(index) << ',' << SpectrumBinUpperEdge(index) << ','
             << fTotalDownstreamPhotonSpectrum[static_cast<std::size_t>(index)] << '\n';
  }
  for (const auto& [particleName, bins] : fSecondarySpectrum) {
    for (G4int index = 0; index < kSpectrumBinCount; ++index) {
      spectrum << "secondary," << particleName << ',' << index << ','
               << SpectrumBinLowerEdge(index) << ',' << SpectrumBinUpperEdge(index) << ','
               << bins[static_cast<std::size_t>(index)] << '\n';
    }
  }

  G4cout << "\nShieldLab-G4 results written to " << fOutputDirectory << G4endl;
  if (!fSecondaryCount.empty()) {
    G4cout << "Secondary particle species tallied: " << fSecondaryCount.size() << G4endl;
    for (const auto& [name, count] : sorted) {
      G4cout << "  " << name << ": " << count << " secondaries downstream\n";
    }
  }
}

void RunAction::AccumulateEvent(const std::vector<G4double>& layerEdep, G4bool transmitted,
                                G4bool reflected)
{
  ++fEvents;
  if (transmitted) {
    ++fTransmitted;
  }
  if (reflected) {
    ++fReflected;
  }
  if (fLayerEdep.size() < layerEdep.size()) {
    fLayerEdep.resize(layerEdep.size(), 0.);
  }
  for (std::size_t index = 0; index < layerEdep.size(); ++index) {
    fLayerEdep[index] += layerEdep[index];
  }
  // Phase 1: batch-means accumulator (10 batches by default).
  ++fCurrentBatchEvents;
  if (transmitted) ++fCurrentBatchTransmitted;
  const G4int batchSize = fEvents > 0 ? std::max(1, fEvents / 10) : 1;
  if (fCurrentBatchEvents >= batchSize) {
    fBatchTransmitted.push_back(fCurrentBatchTransmitted);
    fBatchEvents.push_back(fCurrentBatchEvents);
    fCurrentBatchTransmitted = 0;
    fCurrentBatchEvents = 0;
  }
}

void RunAction::AccumulateSecondary(const G4String& particleName, G4double kineticEnergy_MeV)
{
  fSecondaryCount[particleName] += 1;
  fSecondaryEnergy[particleName] += kineticEnergy_MeV;
  auto& bins = fSecondarySpectrum[particleName];
  if (bins.empty()) {
    bins.assign(kSpectrumBinCount, 0);
  }
  const G4int binIndex = SpectrumBinIndex(kineticEnergy_MeV);
  if (binIndex >= 0) {
    bins[static_cast<std::size_t>(binIndex)] += 1;
  }
}

void RunAction::AccumulateLayerDose(G4int layerIdx, G4double doseGy, G4double edepMeV)
{
  const auto idx = static_cast<std::size_t>(layerIdx);
  if (idx >= fLayerDoseGy.size()) {
    fLayerDoseGy.resize(idx + 1, 0.);
    fLayerEdepSD.resize(idx + 1, 0.);
  }
  fLayerDoseGy[idx] += doseGy;
  fLayerEdepSD[idx] += edepMeV;
}

void RunAction::AccumulateDownstreamPhoton(
  G4int primaryCount,
  G4int totalCount,
  G4double primaryEnergyMeV,
  G4double totalEnergyMeV
)
{
  fPrimaryDownstreamPhotonCount += primaryCount;
  fTotalDownstreamPhotonCount += totalCount;
  fPrimaryDownstreamPhotonEnergyMeV += primaryEnergyMeV;
  fTotalDownstreamPhotonEnergyMeV += totalEnergyMeV;
}

void RunAction::AccumulateDownstreamPhotonSample(G4bool isPrimary, G4double kineticEnergy_MeV)
{
  const G4int binIndex = SpectrumBinIndex(kineticEnergy_MeV);
  if (binIndex < 0) {
    return;
  }
  fTotalDownstreamPhotonSpectrum[static_cast<std::size_t>(binIndex)] += 1;
  if (isPrimary) {
    fPrimaryDownstreamPhotonSpectrum[static_cast<std::size_t>(binIndex)] += 1;
  }
}

void RunAction::SetOutputDirectory(const G4String& value)
{
  fOutputDirectory = value;
}

void RunAction::EnsureOutputDirectory() const
{
  std::filesystem::create_directories(std::filesystem::path(fOutputDirectory.data()));
}
