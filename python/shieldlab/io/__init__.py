__all__ = [
	"collect_composition_sweep",
	"collect_sweep",
	"collect_thickness_sweep",
	"macro_from_study",
	"run_study",
	"validate_study",
	"validate_study_file",
	"write_macro",
	"write_workbook",
]


def __getattr__(name: str):
	if name == "write_workbook":
		from .excel_writer import write_workbook

		return write_workbook
	if name in {"macro_from_study", "write_macro"}:
		from .macro_writer import macro_from_study, write_macro

		return {"macro_from_study": macro_from_study, "write_macro": write_macro}[name]
	if name == "collect_sweep":
		from .sweep_collector import collect_sweep

		return collect_sweep
	if name == "collect_thickness_sweep":
		from .sweep_collector import collect_thickness_sweep

		return collect_thickness_sweep
	if name == "collect_composition_sweep":
		from .sweep_collector import collect_composition_sweep

		return collect_composition_sweep
	if name == "run_study":
		from .runner import run_study

		return run_study
	if name in {"validate_study", "validate_study_file"}:
		from .study_validator import validate_study, validate_study_file

		return {"validate_study": validate_study, "validate_study_file": validate_study_file}[name]
	raise AttributeError(name)