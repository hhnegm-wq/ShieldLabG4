from __future__ import annotations

import math


def attenuation_from_transmission(transmission: float, thickness_cm: float) -> float:
    if thickness_cm <= 0:
        raise ValueError("thickness_cm must be positive")
    if not 0 < transmission <= 1:
        raise ValueError("transmission must be in the interval (0, 1]")
    return -math.log(transmission) / thickness_cm


def mean_free_path(mu_cm_inv: float) -> float:
    if mu_cm_inv <= 0:
        return math.inf
    return 1.0 / mu_cm_inv


def hvl(mu_cm_inv: float) -> float:
    if mu_cm_inv <= 0:
        return math.inf
    return math.log(2.0) / mu_cm_inv


def tvl(mu_cm_inv: float) -> float:
    if mu_cm_inv <= 0:
        return math.inf
    return math.log(10.0) / mu_cm_inv