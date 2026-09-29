from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from agentnative.packs.models import EvalScenario, EvalScenarioCategory, Pack


@dataclass(frozen=True)
class EvalResult:
    scenario_id: str
    passed: bool
    observed_outcome: str
    expected_outcome: str


class PackEvalHarness:
    """Run a pack corpus without coupling sector scenarios to core execution."""

    def validate_corpus(self, pack: Pack) -> None:
        required = set(EvalScenarioCategory)
        missing = required - pack.scenario_categories()
        if missing:
            raise ValueError(f"{pack.pack_id} corpus missing categories: {', '.join(sorted(item.value for item in missing))}")

    def run(self, pack: Pack, evaluator: Callable[[EvalScenario], str]) -> list[EvalResult]:
        self.validate_corpus(pack)
        results = []
        for scenario in pack.evaluation_scenarios:
            observed = evaluator(scenario)
            results.append(EvalResult(scenario.scenario_id, observed == scenario.expected_outcome, observed, scenario.expected_outcome))
        return results


__all__ = ["EvalResult", "PackEvalHarness"]
