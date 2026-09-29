"""Small, production-seam mutation runner used by the Phase 2B audit."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MutationCase:
    mutation_id: str
    control: str
    mutation: str
    baseline: Callable[[], bool]
    mutated: Callable[[], bool]


@dataclass(frozen=True)
class MutationResult:
    mutation_id: str
    control: str
    mutation: str
    expected_test_failure: bool
    actual_result: bool
    caught: bool


class MutationHarness:
    """Compare a production control with a single injected control mutation."""

    def run(self, cases: list[MutationCase]) -> list[MutationResult]:
        results: list[MutationResult] = []
        for case in cases:
            baseline_holds = bool(case.baseline())
            mutated_holds = bool(case.mutated())
            results.append(
                MutationResult(
                    case.mutation_id,
                    case.control,
                    case.mutation,
                    True,
                    mutated_holds,
                    baseline_holds != mutated_holds,
                )
            )
        return results


__all__ = ["MutationCase", "MutationHarness", "MutationResult"]
