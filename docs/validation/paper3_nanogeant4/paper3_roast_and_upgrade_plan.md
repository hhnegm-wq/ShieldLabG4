# Paper 3 Roast and Upgrade Plan

## No-Holds-Barred Roast

This draft is intellectually ambitious and operationally under-armed.

The good news is that the core thesis is publishable: there is a real paper here, because most shielding papers casually say "nanocomposite" while simulating a bulk homogeneous material and never quantify where that shortcut breaks. That is a legitimate methodological gap.

The bad news is that the draft currently behaves more like a sharp protocol memo than a finished scientific paper. It reads as if the results already exist, but the platform does not yet deliver the full evidence stack the text implies. The manuscript is strongest where it explains what *should* be measured and weakest where a reviewer will ask the only question that matters: "Show me the executable evidence path from composition definition to benchmark output to figure to claim."

In blunt terms:

- The paper is selling rigor before the repo has fully earned rigor for this campaign.
- The regime map is the headline contribution, but today it is still a promised artifact, not a generated one.
- The hybrid RVE workflow is conceptually strong, but without an executable benchmark harness it is still architecture, not evidence.
- The paper claims reproducibility in the language of a mature benchmark platform, while paper-3 currently lacks a paper-specific run surface, manifest, and figure pipeline.
- The argument is physics-aware, but still vulnerable to a reviewer saying: "This is a methods proposal with a literature intro, not yet a results paper."

The manuscript is therefore in the dangerous middle state: too technical to be a perspective article, not yet instrumented enough to be a robust methods/results paper.

## Executive Roast

The draft is good enough to justify building the campaign, not good enough to submit.

Right now paper 3 has three asymmetries:

1. The writing is ahead of the implementation.
2. The platform capability is ahead of the paper-specific execution surface.
3. The claimed reproducibility is ahead of the committed paper-3 artifacts.

If submitted in the current state, the likely reviewer reaction is:

- "Important question, but the evidence chain is incomplete."
- "Too many future-tense results and not enough generated data."
- "The homogeneous regime is executable, but the explicit-regime and figure-generation story is not yet locked down."

## Structural Weaknesses

### Technical Weaknesses

| ID | Weakness | Severity | Why it matters |
|---|---|---|---|
| T1 | No paper-3 specific executable benchmark surface | Critical | The repo can run studies, but paper 3 did not yet have a dedicated study + manifest + orchestration entry point. |
| T2 | No paper-3 baseline study pack committed for regime A | Critical | Without a locked baseline study, every later comparison risks drifting in composition, density, geometry, or energy grid. |
| T3 | No paper-3 benchmark planner tying study -> macro -> manifest | High | Reproducibility claims remain rhetorical until the planning artifact exists in-code. |
| T4 | No paper-3 focused regression tests | High | Without narrow tests, later implementation work will silently erode the benchmark contract. |
| T5 | No paper-3 figure/result generation path yet committed | High | The manuscript defines figures F1-F8, but the platform cannot yet deterministically emit them for this campaign. |
| T6 | No explicit-regime implementation yet for B/C/D | High | The whole paper hinges on cross-regime comparison; only the regime-A side is currently realistic. |
| T7 | No locked WSL execution runbook for paper 3 | Medium | Actual Geant4 runs will become fragile and operator-dependent without a pinned invocation path. |

### Product / Scientific Weaknesses

| ID | Weakness | Severity | Why it matters |
|---|---|---|---|
| P1 | The paper still looks like a protocol disguised as a results paper | Critical | Reviewers will tolerate design intent in v02, but not in a submission draft. |
| P2 | The evidence ladder is missing one layer between manuscript claims and repo artifacts | Critical | Every major claim needs a named artifact, not just a planned section. |
| P3 | Density provenance is not locked | High | Reviewer confidence collapses if density inputs are estimated but presented like measured values. |
| P4 | Experimental anchor references for Bi2O3/WO3/BaSO4 systems are still placeholders | High | That leaves the manuscript exposed on materials realism and benchmarking relevance. |
| P5 | Statistical acceptance is defined, but not yet enforced in-code for paper 3 | High | A pre-registered threshold that is not executable is just prose. |

## Upgrade Roadmap

The rule for execution is strict: finish one weakness fully, validate it, then move to the next.

### Step 1 - Resolve T1/T2/T3 together: create the paper-3 executable baseline

Deliverables:
- A committed paper-3 regime-A baseline study JSON.
- A paper-3 benchmark planner module that validates the study, writes the Geant4 macro, and emits a benchmark manifest.
- A benchmark manifest that states regime, campaign, energy points, materials, and artifact hashes.

Definition of done:
- The study validates with zero errors.
- The planner writes a macro and manifest deterministically.
- A focused pytest slice passes.

### Step 2 - Resolve T4: add narrow regression tests

Deliverables:
- Test that the paper-3 study validates cleanly.
- Test that the planner expands a nanocomposite study into a mass-fraction Geant4 macro.
- Test that the manifest contains the expected paper-3 metadata.

Definition of done:
- All new tests pass.
- Existing benchmark pipeline tests still pass.

### Step 3 - Resolve T7: lock the WSL execution path

Deliverables:
- A single documented invocation for paper-3 runs in WSL.
- A first successful regime-A run producing result artifacts.
- Stored output path under `build/results/paper3_nano/` or equivalent campaign directory.

Definition of done:
- One baseline run completes from study JSON to output artifacts.
- Validation summary or equivalent manifest is generated.

### Step 4 - Resolve T5/P5: add figure/result and acceptance enforcement

Deliverables:
- Paper-3 result aggregator.
- Figure generator for at least F3 and F6 from generated data.
- Executable hypothesis checks matching section 4.5 of the manuscript.

Definition of done:
- A generated CSV/JSON result table exists.
- At least two manuscript figures are produced from committed code.
- Acceptance pass/fail is machine-readable.

### Step 5 - Resolve T6: implement explicit-regime scaffolding

Deliverables:
- Initial regime-B RVE explicit geometry surface.
- Initial regime-C multi-union surface.
- Stub regime-D correction-map workflow with manifest schema.

Definition of done:
- Regime B/C build paths exist and compile.
- Each regime has at least one smoke benchmark definition.

### Step 6 - Resolve P3/P4/P1/P2: convert protocol into submission-grade evidence

Deliverables:
- Density provenance table with source tags.
- DOI-verified benchmark references for the materials families.
- v03 manuscript with generated figures/results replacing forward-looking claims.

Definition of done:
- No placeholder density/reference tags remain in the submission draft.
- Every major claim points to a committed artifact.

## Fix Log

| Order | Weaknesses addressed | Status | Validation |
|---|---|---|---|
| 1 | T1 + T2 + T3 + T4 | Done in this session | Added paper-3 regime-A study, planner module, and focused tests |
| 2 | T7 | In progress this session | WSL execution attempted after tests |
| 3 | T5 + P5 | Queued | Pending generated result tables/figures |
| 4 | T6 | Queued | Pending explicit-regime implementation |
| 5 | P3 + P4 + P1 + P2 | Queued | Pending evidence completion |

## Enterprise / Robust Scientific Grade Target State

Paper 3 reaches enterprise-grade scientific quality only when all of the following are true:

- Every manuscript claim can be traced to a generated artifact.
- Every generated artifact can be traced to a committed study file and macro.
- Every study file validates automatically.
- Every acceptance threshold is executable.
- Every figure is regenerated by code, not hand-assembled.
- Every WSL/Geant4 run is reproducible from one documented command.
- Every density/reference input has provenance.

Anything short of that is still a promising draft, not a submission-grade benchmark paper.
