# ShieldLab G4 Manuscript Methods Pack

Generated: 2026-05-05T10:35:29.241341+00:00

## Core Equations

- **Mass attenuation mixture rule**: (mu/rho) = sum_i w_i * (mu/rho)_i
  - NIST mixture rule for compounds and mixtures.
- **Transmission model**: T = exp(-(mu/rho)*rho*x)
  - Narrow-beam attenuation model used for analytical comparison.
- **HVL and TVL**: HVL = ln(2)/mu ; TVL = ln(10)/mu
  - Derived attenuation metrics for shielding studies.
- **Buildup GP model**: B = 1 + (b-1)*(K^x - 1)/(K - 1)
  - GP-based buildup calculation for broad-beam corrections.
- **Normalized residual**: r = (simulation - reference) / sigma_sim
  - Uncertainty-aware residual metric for benchmark diagnostics.

## Assumptions and Validation Context

- release_gate: pass
- q1_readiness: {'no_study_validation_errors': True, 'no_failed_benchmark_sets': True, 'threshold_coverage_ratio': 0.0, 'provenance_coverage_ratio': 0.0, 'citation_coverage_ratio': 1.0, 'statistical_adequacy_ratio': 0.0, 'ready_for_submission': False}
- runtime_result_sets: 2
- threshold_backed_sets: 0
- provenance_manifest_sets: 0
- benchmark_status_counts: {'unavailable': 2}

## Uncertainty Statements

- Transmission, reflection, and absorption uncertainty are propagated with binomial standard-error models.
- 95% confidence half-widths are reported for event fractions when count statistics are available.
- Linear and mass attenuation uncertainty are propagated through delta-method conversion from transmission uncertainty.
- Benchmark normalized residuals are reported as (simulation - literature) / simulation standard error.
- Uncertainty interpretation must distinguish statistical, input, model, and literature components.

## Bibliography

- Exploring the potential of attapulgite clay composites containing intercalated nano-cadmium oxide and nano-nickel oxide for efficient radiation shielding applications. DOI: 10.1016/j.radphyschem.2024.112149 (https://doi.org/10.1016/j.radphyschem.2024.112149)
- Evaluation of shielding properties of a developed nanocomposite. DOI: 10.1088/1402-4896/ad3b48 (https://doi.org/10.1088/1402-4896/ad3b48)
- A new nanocomposite of copper oxide and magnetite intercalated into attapulgite clay. DOI: 10.1016/j.radphyschem.2023.111398 (https://doi.org/10.1016/j.radphyschem.2023.111398)
- Evaluation of Radiation Shielding Parameters of Different Metallic Glass Compositions for alpha, beta, gamma, n, and p Radiation. DOI: 10.1007/s11664-025-11830-w (https://doi.org/10.1007/s11664-025-11830-w)
- Electronic polarizability, dielectric and gamma-ray shielding features of PbO-P2O5-Na2O-Al2O3 glasses doped with MoO3. DOI: 10.1007/s10854-020-04709-5 (https://doi.org/10.1007/s10854-020-04709-5)
- A Comprehensive Investigation of the Impact of NiO on the Radiation Attenuation Characteristics of (CaO-Li2O-NiO-SiO2) Glass Structure. DOI: 10.1007/s11664-023-10833-9 (https://doi.org/10.1007/s11664-023-10833-9)

## Benchmark Table Artifact

- CSV: d:\projects\ShieldLabG4\docs\validation\methods_benchmark_table_20260505_103529.csv
