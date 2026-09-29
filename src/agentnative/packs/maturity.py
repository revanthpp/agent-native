from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Mapping


class MaturityLevel(IntEnum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3
    L4 = 4
    L5 = 5


LEVEL_NAMES = {
    MaturityLevel.L0: "Invisible",
    MaturityLevel.L1: "Discoverable",
    MaturityLevel.L2: "Understandable",
    MaturityLevel.L3: "Callable",
    MaturityLevel.L4: "Transactable",
    MaturityLevel.L5: "Orchestratable",
}


@dataclass(frozen=True)
class DimensionAssessment:
    dimension: str
    level: MaturityLevel
    level_name: str
    satisfied_gates: tuple[str, ...]
    missing_gates: tuple[str, ...]


@dataclass(frozen=True)
class MaturityAssessment:
    dimensions: tuple[DimensionAssessment, ...]

    def dimension(self, name: str) -> DimensionAssessment:
        for item in self.dimensions:
            if item.dimension == name:
                return item
        raise KeyError(name)

    def to_dict(self) -> dict[str, object]:
        return {
            "dimensions": {
                item.dimension: {
                    "level": item.level.name,
                    "level_name": item.level_name,
                    "satisfied_gates": list(item.satisfied_gates),
                    "missing_gates": list(item.missing_gates),
                }
                for item in self.dimensions
            }
        }


class MaturityFramework:
    """Evidence-gated, multidimensional maturity with no composite score."""

    def assess(self, gates_by_dimension: Mapping[str, Mapping[int, Mapping[str, bool]]]) -> MaturityAssessment:
        assessments = []
        for dimension, gates_by_level in sorted(gates_by_dimension.items()):
            achieved = MaturityLevel.L0
            satisfied: list[str] = []
            missing: list[str] = []
            for level in range(1, 6):
                if level not in gates_by_level:
                    missing.append(f"L{level}:criteria_not_declared")
                    break
                gates = gates_by_level[level]
                if not gates:
                    missing.append(f"L{level}:criteria_not_declared")
                    break
                level_missing = [name for name, result in gates.items() if not result]
                if level_missing:
                    missing.extend(f"L{level}:{name}" for name in level_missing)
                    break
                achieved = MaturityLevel(level)
                satisfied.extend(f"L{level}:{name}" for name in gates)
            assessments.append(DimensionAssessment(dimension, achieved, LEVEL_NAMES[achieved], tuple(satisfied), tuple(missing)))
        return MaturityAssessment(tuple(assessments))


__all__ = ["DimensionAssessment", "MaturityAssessment", "MaturityFramework", "MaturityLevel"]
