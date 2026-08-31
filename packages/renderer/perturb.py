"""Small perturbation helpers for handwritten-style rendering.

This module is intentionally minimal for V1. Later commits can expand it with
baseline jitter, spacing variation, slant transforms, and stroke variation.
"""

from __future__ import annotations

import random


def jitter_int(base_value: int, max_abs_jitter: int, rng: random.Random) -> int:
    """Return an integer value with bounded random jitter applied."""
    if max_abs_jitter <= 0:
        return base_value

    return base_value + rng.randint(-max_abs_jitter, max_abs_jitter)


def jitter_scale(max_abs_jitter: float, rng: random.Random) -> float:
    """Return a positive scale factor with bounded random jitter."""
    if max_abs_jitter <= 0:
        return 1.0

    bounded_jitter = min(max_abs_jitter, 0.95)
    return 1.0 + rng.uniform(-bounded_jitter, bounded_jitter)
