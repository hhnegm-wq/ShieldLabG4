"""G-P buildup factor self-consistency regression test (Phase 1 scaffold).

This is **not** a literature cross-check. It guards against accidental
drift in :func:`shieldlab.physics.shielding_params.gp_buildup_factor` or
in the shipped GP coefficient tables. When the licensed
ANSI/ANS-6.4.3-1991 reference data is added under ``data/references/``
this test will graduate to a true validation. See the docstring of
``shieldlab.physics.buildup_validation`` for the rationale.
"""
from __future__ import annotations

import pytest

from shieldlab.physics.buildup_validation import REF_BUILDUP, validate_all


@pytest.mark.publication
@pytest.mark.parametrize("material", sorted(REF_BUILDUP))
def test_buildup_self_consistency(material: str) -> None:
    res = validate_all()[material]
    assert res.max_abs_residual < 1e-9, (
        f"{material}: max |Δ|/B = {res.max_abs_residual:.3e}\n"
        f"reference=\n{res.reference}\ncomputed=\n{res.computed}"
    )
