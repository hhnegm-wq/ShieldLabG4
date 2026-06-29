from shieldlab.io.release_gate import GatePolicy, evaluate_release_gate, policy_for_profile


def _sample_report(
    *,
    study_errors: int,
    failed_sets: int,
    threshold: float,
    provenance: float,
    citation: float,
    statistical: float,
    ready: bool,
):
    return {
        "summary": {
            "study_error_count": study_errors,
            "failed_benchmark_sets": failed_sets,
            "q1_readiness": {
                "threshold_coverage_ratio": threshold,
                "provenance_coverage_ratio": provenance,
                "citation_coverage_ratio": citation,
                "statistical_adequacy_ratio": statistical,
                "ready_for_submission": ready,
            },
        }
    }


def test_release_gate_passes_when_policy_is_satisfied():
    policy = GatePolicy(
        max_study_errors=0,
        max_failed_benchmark_sets=0,
        min_threshold_coverage=0.90,
        min_provenance_coverage=0.90,
        min_citation_coverage=0.90,
        min_statistical_adequacy=0.80,
        require_ready_for_submission=True,
    )
    report = _sample_report(
        study_errors=0,
        failed_sets=0,
        threshold=1.0,
        provenance=1.0,
        citation=1.0,
        statistical=1.0,
        ready=True,
    )

    passed, reasons = evaluate_release_gate(report, policy)

    assert passed is True
    assert reasons == []


def test_release_gate_fails_with_multiple_reasons():
    policy = GatePolicy(
        max_study_errors=0,
        max_failed_benchmark_sets=0,
        min_threshold_coverage=0.95,
        min_provenance_coverage=0.95,
        min_citation_coverage=0.95,
        min_statistical_adequacy=0.90,
        require_ready_for_submission=True,
    )
    report = _sample_report(
        study_errors=2,
        failed_sets=1,
        threshold=0.8,
        provenance=0.9,
        citation=0.5,
        statistical=0.7,
        ready=False,
    )

    passed, reasons = evaluate_release_gate(report, policy)

    assert passed is False
    assert any("study_error_count=" in reason for reason in reasons)
    assert any("failed_benchmark_sets=" in reason for reason in reasons)
    assert any("threshold_coverage_ratio=" in reason for reason in reasons)
    assert any("provenance_coverage_ratio=" in reason for reason in reasons)
    assert any("citation_coverage_ratio=" in reason for reason in reasons)
    assert any("statistical_adequacy_ratio=" in reason for reason in reasons)
    assert any("ready_for_submission" in reason for reason in reasons)


def test_gate_profiles_have_expected_strictness_order():
    release = policy_for_profile("release")
    dev = policy_for_profile("dev")

    assert release.max_study_errors <= dev.max_study_errors
    assert release.max_failed_benchmark_sets <= dev.max_failed_benchmark_sets
    assert release.min_threshold_coverage >= dev.min_threshold_coverage
    assert release.min_provenance_coverage >= dev.min_provenance_coverage
    assert release.min_citation_coverage >= dev.min_citation_coverage
    assert release.min_statistical_adequacy >= dev.min_statistical_adequacy
