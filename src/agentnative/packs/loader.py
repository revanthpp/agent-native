from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml

from agentnative import __version__
from agentnative.packs.models import CapabilityProfile, EvalScenario, EvalScenarioCategory, Pack, PackManifest
from agentnative.protocols.models import ActionClass, SideEffect


class PackCompatibilityError(ValueError):
    """Raised when a pack is invalid or incompatible with the core."""


_REQUIRED_MANIFEST = {
    "pack_id",
    "pack_version",
    "sector",
    "subsectors",
    "core_version_requirement",
    "release_status",
}
_REQUIRED_TOP_LEVEL = {
    "manifest",
    "capability_taxonomy",
    "risk_model",
    "maturity_model",
    "control_profiles",
    "activation_strategies",
    "human_handoff_rules",
    "evaluation_scenarios",
    "evidence_requirements",
    "report_sections",
    "dependencies",
}
_REQUIRED_EVAL_CATEGORIES = set(EvalScenarioCategory)


def _as_tuple(value: Any, field_name: str) -> tuple[Any, ...]:
    if not isinstance(value, list):
        raise PackCompatibilityError(f"{field_name} must be a list")
    return tuple(value)


def _version_parts(value: str) -> tuple[int, int, int]:
    import re

    match = re.fullmatch(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?.*", value.strip())
    if not match:
        raise PackCompatibilityError(f"invalid version: {value}")
    return tuple(int(part or 0) for part in match.groups())


def _satisfies(version: str, requirement: str) -> bool:
    current = _version_parts(version)
    for clause in (part.strip() for part in requirement.split(",")):
        if not clause:
            continue
        operator = next((item for item in (">=", "<=", ">", "<", "==") if clause.startswith(item)), "==")
        expected = _version_parts(clause[len(operator) :])
        if operator == ">=" and not current >= expected:
            return False
        if operator == "<=" and not current <= expected:
            return False
        if operator == ">" and not current > expected:
            return False
        if operator == "<" and not current < expected:
            return False
        if operator == "==" and not current == expected:
            return False
    return True


class PackLoader:
    def __init__(self, *, core_version: str = __version__) -> None:
        self.core_version = core_version

    def load_file(self, path: str | Path) -> Pack:
        source = Path(path)
        try:
            raw = yaml.safe_load(source.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PackCompatibilityError(f"could not read pack {source}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise PackCompatibilityError(f"pack {source} is not valid YAML: {exc}") from exc
        return self.load_dict(raw, source=str(source))

    def load_dict(self, raw: Any, *, source: str = "<memory>") -> Pack:
        if not isinstance(raw, dict):
            raise PackCompatibilityError(f"pack {source} must be an object")
        missing = _REQUIRED_TOP_LEVEL - set(raw)
        if missing:
            raise PackCompatibilityError(f"pack {source} missing fields: {', '.join(sorted(missing))}")
        manifest_raw = raw["manifest"]
        if not isinstance(manifest_raw, dict):
            raise PackCompatibilityError(f"pack {source} manifest must be an object")
        missing = _REQUIRED_MANIFEST - set(manifest_raw)
        if missing:
            raise PackCompatibilityError(f"pack {source} manifest missing fields: {', '.join(sorted(missing))}")
        if not _satisfies(self.core_version, str(manifest_raw["core_version_requirement"])):
            raise PackCompatibilityError(
                f"pack {manifest_raw.get('pack_id', source)} requires core "
                f"{manifest_raw['core_version_requirement']}, found {self.core_version}"
            )
        if not str(manifest_raw["pack_id"]).startswith("sector."):
            raise PackCompatibilityError("pack_id must use the sector.<name> namespace")

        capabilities = []
        for raw_capability in _as_tuple(raw["capability_taxonomy"], "capability_taxonomy"):
            if not isinstance(raw_capability, dict):
                raise PackCompatibilityError("each capability must be an object")
            required = {"capability_id", "name", "group"} - set(raw_capability)
            if required:
                raise PackCompatibilityError(f"capability missing fields: {', '.join(sorted(required))}")
            try:
                capabilities.append(
                    CapabilityProfile(
                        capability_id=str(raw_capability["capability_id"]),
                        name=str(raw_capability["name"]),
                        group=str(raw_capability["group"]),
                        action_class=ActionClass(str(raw_capability.get("action_class", "UNKNOWN")).upper()),
                        side_effect=SideEffect(str(raw_capability.get("side_effect", "UNKNOWN")).upper()),
                        resource_types=tuple(str(item) for item in raw_capability.get("resource_types", [])),
                        required_scopes=tuple(str(item) for item in raw_capability.get("required_scopes", [])),
                        reversibility=str(raw_capability.get("reversibility", "unknown")),
                        confirmation=str(raw_capability.get("confirmation", "unknown")),
                        idempotency=str(raw_capability.get("idempotency", "unknown")),
                        data_sensitivity=str(raw_capability.get("data_sensitivity", "unknown")),
                        human_escalation=bool(raw_capability.get("human_escalation", False)),
                        description=str(raw_capability.get("description", "")),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise PackCompatibilityError(f"invalid capability in {source}: {exc}") from exc

        scenarios = []
        for raw_scenario in _as_tuple(raw["evaluation_scenarios"], "evaluation_scenarios"):
            if not isinstance(raw_scenario, dict):
                raise PackCompatibilityError("each evaluation scenario must be an object")
            required = {"scenario_id", "requirement_id", "category", "title", "expected_outcome"} - set(raw_scenario)
            if required:
                raise PackCompatibilityError(f"scenario missing fields: {', '.join(sorted(required))}")
            try:
                scenarios.append(
                    EvalScenario(
                        scenario_id=str(raw_scenario["scenario_id"]),
                        requirement_id=str(raw_scenario["requirement_id"]),
                        category=EvalScenarioCategory(str(raw_scenario["category"])),
                        title=str(raw_scenario["title"]),
                        expected_outcome=str(raw_scenario["expected_outcome"]),
                        capability_id=str(raw_scenario["capability_id"]) if raw_scenario.get("capability_id") else None,
                        tags=tuple(str(item) for item in raw_scenario.get("tags", [])),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise PackCompatibilityError(f"invalid evaluation scenario in {source}: {exc}") from exc

        if len({item.capability_id for item in capabilities}) != len(capabilities):
            raise PackCompatibilityError(f"pack {manifest_raw['pack_id']} contains duplicate capability IDs")
        if len({item.scenario_id for item in scenarios}) != len(scenarios):
            raise PackCompatibilityError(f"pack {manifest_raw['pack_id']} contains duplicate scenario IDs")
        missing_categories = _REQUIRED_EVAL_CATEGORIES - {item.category for item in scenarios}
        if missing_categories:
            raise PackCompatibilityError(
                f"pack {manifest_raw['pack_id']} evaluation corpus missing categories: "
                f"{', '.join(sorted(item.value for item in missing_categories))}"
            )

        manifest_fields = {item.name for item in fields(PackManifest)}
        manifest_values = {key: manifest_raw[key] for key in manifest_fields if key in manifest_raw}
        for key in ("subsectors", "protocol_profiles", "platform_profiles", "known_limitations", "external_reference_mappings"):
            if key in manifest_values:
                manifest_values[key] = tuple(manifest_values[key])
        manifest = PackManifest(**manifest_values)
        return Pack(
            manifest=manifest,
            capabilities=tuple(capabilities),
            risk_model=raw["risk_model"],
            maturity_model=raw["maturity_model"],
            control_profiles=raw["control_profiles"],
            activation_strategies=_as_tuple(raw["activation_strategies"], "activation_strategies"),
            human_handoff_rules=_as_tuple(raw["human_handoff_rules"], "human_handoff_rules"),
            evaluation_scenarios=tuple(scenarios),
            evidence_requirements=raw["evidence_requirements"],
            report_sections=_as_tuple(raw["report_sections"], "report_sections"),
            dependencies=raw["dependencies"],
        )


class PackRegistry:
    def __init__(self, packs: list[Pack] | None = None) -> None:
        self._packs = {pack.pack_id: pack for pack in packs or []}
        self._disabled: set[str] = set()

    def register(self, pack: Pack) -> None:
        if pack.pack_id in self._packs:
            raise ValueError(f"pack already registered: {pack.pack_id}")
        self._packs[pack.pack_id] = pack

    def disable(self, pack_id: str) -> None:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        self._disabled.add(pack_id)

    def enable(self, pack_id: str) -> None:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        self._disabled.discard(pack_id)

    def get(self, pack_id: str, *, include_disabled: bool = False) -> Pack:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        if not include_disabled and pack_id in self._disabled:
            raise KeyError(f"pack is disabled: {pack_id}")
        return self._packs[pack_id]

    def list(self, *, include_disabled: bool = False) -> list[Pack]:
        return [pack for pack_id, pack in sorted(self._packs.items()) if include_disabled or pack_id not in self._disabled]

    def status(self) -> dict[str, str]:
        return {pack_id: "DISABLED" if pack_id in self._disabled else "ACTIVE" for pack_id in sorted(self._packs)}


def load_builtin_packs() -> PackRegistry:
    directory = Path(__file__).with_name("builtin")
    loader = PackLoader()
    return PackRegistry([loader.load_file(path) for path in sorted(directory.glob("*.yaml"))])


__all__ = ["PackCompatibilityError", "PackLoader", "PackRegistry", "load_builtin_packs"]
