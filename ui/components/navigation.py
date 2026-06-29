from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class PageSpec:
    key: str
    file_name: str
    title: str
    icon: str
    section: str
    route: str
    default: bool = False


@dataclass(frozen=True)
class QuickActionSpec:
    label: str
    page_key: str
    tone: str
    title: str


@dataclass(frozen=True)
class WorkflowSpec:
    key: str
    title: str
    body: str
    icon: str
    start_page_key: str
    stage_page_keys: tuple[str, ...]


PAGE_SPECS: tuple[PageSpec, ...] = (
    PageSpec("home", "home.py", "Home", ":material/dashboard:", "", "/", default=True),
    PageSpec("study_builder", "study_builder.py", "Study Builder", ":material/science:", "Simulation", "/study_builder"),
    PageSpec("run_study", "run_study.py", "Run Study", ":material/play_circle:", "Simulation", "/run_study"),
    PageSpec("shielding_calculator", "shielding_calculator.py", "Shielding Calculator", ":material/calculate:", "Analysis", "/shielding_calculator"),
    PageSpec("comparison", "comparison.py", "Material Comparison", ":material/bar_chart:", "Analysis", "/comparison"),
    PageSpec("dose_rate", "dose_rate.py", "Dose-Rate Calculator", ":material/radiology:", "Analysis", "/dose_rate"),
    PageSpec("results_explorer", "results_explorer.py", "Results Explorer", ":material/search:", "Analysis", "/results_explorer"),
    PageSpec("literature_benchmarks", "literature_benchmarks.py", "Literature Benchmarks", ":material/menu_book:", "Analysis", "/literature_benchmarks"),
    PageSpec("benchmark_dashboard", "benchmark_dashboard.py", "Benchmark Dashboard", ":material/insights:", "Analysis", "/benchmark_dashboard"),
    PageSpec("methods", "methods.py", "Methods & References", ":material/description:", "Reference", "/methods"),
    PageSpec("about", "about.py", "About & Legal", ":material/info:", "Reference", "/about"),
    PageSpec("settings", "settings.py", "Settings", ":material/settings:", "Platform", "/settings"),
)

PAGE_BY_KEY = {spec.key: spec for spec in PAGE_SPECS}
NAV_SECTION_LABELS: tuple[str, ...] = ("Simulation", "Analysis", "Reference", "Platform")

# Workflow entry-point pages surfaced as the primary nav section.
# These appear under "Workflows" first; they are removed from their original
# section buckets so each page only appears once.
# Must stay in sync with PRIMARY_WORKFLOWS.start_page_key values.
WORKFLOW_ENTRY_PAGE_KEYS: tuple[str, ...] = (
    "study_builder",
    "shielding_calculator",
    "benchmark_dashboard",
)

HOME_FEATURE_PAGE_KEYS: tuple[str, ...] = (
    "shielding_calculator",
    "comparison",
    "dose_rate",
    "methods",
)

QUICK_ACTION_SPECS: tuple[QuickActionSpec, ...] = (
    QuickActionSpec(
        label="Configure Study",
        page_key="study_builder",
        tone="green",
        title="Start a simulation workflow from study design",
    ),
    QuickActionSpec(
        label="Run Study",
        page_key="run_study",
        tone="blue",
        title="Launch or monitor Monte Carlo execution",
    ),
    QuickActionSpec(
        label="Review Results",
        page_key="results_explorer",
        tone="violet",
        title="Inspect validated outputs, figures, and exports",
    ),
)

PRIMARY_WORKFLOWS: tuple[WorkflowSpec, ...] = (
    WorkflowSpec(
        key="simulation_delivery",
        title="Plan, Run, Review",
        body="Define inputs, queue the Monte Carlo run, and inspect validated outputs without leaving the primary delivery path.",
        icon="1",
        start_page_key="study_builder",
        stage_page_keys=("study_builder", "run_study", "results_explorer"),
    ),
    WorkflowSpec(
        key="shielding_screening",
        title="Screen Shielding Options",
        body="Move from parameter screening to material comparison and dose-rate consequences as one analysis workflow.",
        icon="2",
        start_page_key="shielding_calculator",
        stage_page_keys=("shielding_calculator", "comparison", "dose_rate"),
    ),
    WorkflowSpec(
        key="validation_evidence",
        title="Review Validation Evidence",
        body="Start from benchmark status, inspect literature alignment, and end at citable methods and references.",
        icon="3",
        start_page_key="benchmark_dashboard",
        stage_page_keys=("benchmark_dashboard", "literature_benchmarks", "methods"),
    ),
)


def get_page_spec(page_key: str) -> PageSpec:
    return PAGE_BY_KEY[page_key]


def page_href(page_key: str) -> str:
    return get_page_spec(page_key).route


def home_feature_specs() -> tuple[PageSpec, ...]:
    return tuple(get_page_spec(page_key) for page_key in HOME_FEATURE_PAGE_KEYS)


def workflow_stage_specs(workflow: WorkflowSpec) -> tuple[PageSpec, ...]:
    return tuple(get_page_spec(page_key) for page_key in workflow.stage_page_keys)


def visible_page_specs() -> tuple[PageSpec, ...]:
    return PAGE_SPECS


def build_navigation_sections(
    pages_dir: Path,
    page_factory: Callable[..., object],
) -> dict[str, list[object]]:
    # "Workflows" section appears first so the sidebar leads with task context,
    # not a flat page inventory.  Workflow entry-point pages are surfaced here
    # and removed from their normal section buckets to avoid duplication.
    sections: dict[str, list[object]] = {"": [], "Workflows": []}
    for label in NAV_SECTION_LABELS:
        sections[label] = []

    for spec in PAGE_SPECS:
        page = page_factory(
            str(pages_dir / spec.file_name),
            title=spec.title,
            icon=spec.icon,
            default=spec.default,
        )
        if spec.key in WORKFLOW_ENTRY_PAGE_KEYS:
            sections["Workflows"].append(page)
        else:
            sections[spec.section].append(page)

    return sections