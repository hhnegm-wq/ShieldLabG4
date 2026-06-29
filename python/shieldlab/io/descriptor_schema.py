from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class DescriptorRow:
    parameter: str
    value: float | str | bool


def _coerce_descriptor_value(value: Any) -> float | str | bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if value is None:
        return ""
    if isinstance(value, str):
        vv = value.strip()
        try:
            return float(vv)
        except ValueError:
            return vv
    return str(value)


def descriptor_mapping_to_rows(payload: Mapping[str, Any]) -> list[DescriptorRow]:
    rows: list[DescriptorRow] = []
    for key, value in payload.items():
        rows.append(DescriptorRow(parameter=str(key), value=_coerce_descriptor_value(value)))
    return rows
