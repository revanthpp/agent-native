from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

import yaml

from agentnative import __version__
from agentnative.packs.models import CapabilityProfile, EvalScenario, EvalScenarioCategory, Pack, PackLifecycleState, PackManifest
from agentnative.packs.signing import DependencyLock, PackSignatureError, PackSignatureVerifier, PackTrustPolicy, parse_signature
from agentnative.protocols.models import ActionClass, SideEffect
from agentnative.transactions.core import stable_hash


class PackCompatibilityError(ValueError):
    """Raised when a pack is invalid or incompatible with the core."""


class PackResourceLimitError(PackCompatibilityError):
    pass


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
_TRANSPORT_PROVENANCE_FIELDS = {"source", "publisher", "created_at", "build_id", "content_hash", "signature", "signing_key_id"}


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


def _identity_payload(value: Any, *, in_provenance: bool = False) -> Any:
    """Remove non-semantic transport metadata before hashing a pack."""
    if isinstance(value, dict):
        return {
            str(key): _identity_payload(item, in_provenance=str(key) == "provenance")
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
            if not (in_provenance and str(key) in _TRANSPORT_PROVENANCE_FIELDS)
        }
    if isinstance(value, list):
        return [_identity_payload(item, in_provenance=in_provenance) for item in value]
    return value


def pack_content_hash(raw: dict[str, Any]) -> str:
    return stable_hash(_identity_payload(raw))


class PackLoader:
    def __init__(self, *, core_version: str = __version__, max_bytes: int = 1_000_000, max_depth: int = 20, max_capabilities: int = 1_000, max_scenarios: int = 2_000, max_references: int = 5_000) -> None:
        self.core_version = core_version
        self.max_bytes = max_bytes
        self.max_depth = max_depth
        self.max_capabilities = max_capabilities
        self.max_scenarios = max_scenarios
        self.max_references = max_references

    def load_file(self, path: str | Path) -> Pack:
        source = Path(path)
        try:
            content = source.read_text(encoding="utf-8")
            if len(content.encode("utf-8")) > self.max_bytes:
                raise PackResourceLimitError(f"pack {source} exceeds the manifest size limit")
            raw = yaml.safe_load(content)
        except OSError as exc:
            raise PackCompatibilityError(f"could not read pack {source}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise PackCompatibilityError(f"pack {source} is not valid YAML: {exc}") from exc
        return self.load_dict(raw, source=str(source))

    def load_dict(self, raw: Any, *, source: str = "<memory>") -> Pack:
        if not isinstance(raw, dict):
            raise PackCompatibilityError(f"pack {source} must be an object")
        if _depth(raw) > self.max_depth:
            raise PackResourceLimitError(f"pack {source} exceeds the nesting limit")
        missing = _REQUIRED_TOP_LEVEL - set(raw)
        if missing:
            raise PackCompatibilityError(f"pack {source} missing fields: {', '.join(sorted(missing))}")
        manifest_raw = raw["manifest"]
        if not isinstance(manifest_raw, dict):
            raise PackCompatibilityError(f"pack {source} manifest must be an object")
        manifest_raw = dict(manifest_raw)
        manifest_raw.setdefault("pack_schema_version", "1.0")
        manifest_raw.setdefault("lifecycle_state", "draft" if manifest_raw.get("release_status") == "design" else manifest_raw.get("release_status", "draft"))
        manifest_raw.setdefault("namespace", str(manifest_raw.get("pack_id", "")))
        manifest_raw.setdefault("required_core_guarantees", [])
        manifest_raw.setdefault("provenance", {})
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
        try:
            lifecycle_state = PackLifecycleState(str(manifest_raw["lifecycle_state"]).lower())
        except ValueError as exc:
            raise PackCompatibilityError(f"invalid lifecycle state: {manifest_raw['lifecycle_state']}") from exc
        if str(manifest_raw["namespace"]) != str(manifest_raw["pack_id"]):
            raise PackCompatibilityError("namespace must equal pack_id for sector packs")
        declared_hash = manifest_raw.get("provenance", {}).get("content_hash") if isinstance(manifest_raw.get("provenance"), dict) else None
        content_hash = pack_content_hash(raw)
        if declared_hash and declared_hash != content_hash:
            raise PackCompatibilityError(f"pack content hash mismatch: declared {declared_hash}, computed {content_hash}")

        capabilities = []
        if len(raw["capability_taxonomy"]) > self.max_capabilities:
            raise PackResourceLimitError(f"pack {source} exceeds the capability limit")
        for raw_capability in _as_tuple(raw["capability_taxonomy"], "capability_taxonomy"):
            if not isinstance(raw_capability, dict):
                raise PackCompatibilityError("each capability must be an object")
            required = {"capability_id", "name", "group"} - set(raw_capability)
            if required:
                raise PackCompatibilityError(f"capability missing fields: {', '.join(sorted(required))}")
            try:
                capabilities.append(
                    CapabilityProfile(
                        capability_id=f"{manifest_raw['pack_id']}:{str(raw_capability['capability_id'])}",
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
        if len(raw["evaluation_scenarios"]) > self.max_scenarios:
            raise PackResourceLimitError(f"pack {source} exceeds the scenario limit")
        for raw_scenario in _as_tuple(raw["evaluation_scenarios"], "evaluation_scenarios"):
            if not isinstance(raw_scenario, dict):
                raise PackCompatibilityError("each evaluation scenario must be an object")
            required = {"scenario_id", "requirement_id", "category", "title", "expected_outcome"} - set(raw_scenario)
            if required:
                raise PackCompatibilityError(f"scenario missing fields: {', '.join(sorted(required))}")
            try:
                scenarios.append(
                    EvalScenario(
                        scenario_id=f"{manifest_raw['pack_id']}:{str(raw_scenario['scenario_id'])}",
                        requirement_id=str(raw_scenario["requirement_id"]),
                        category=EvalScenarioCategory(str(raw_scenario["category"])),
                        title=str(raw_scenario["title"]),
                        expected_outcome=str(raw_scenario["expected_outcome"]),
                        capability_id=f"{manifest_raw['pack_id']}:{str(raw_scenario['capability_id'])}" if raw_scenario.get("capability_id") and not str(raw_scenario["capability_id"]).startswith(f"{manifest_raw['pack_id']}:") else str(raw_scenario["capability_id"]) if raw_scenario.get("capability_id") else None,
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
        references = sum(len(str(item)) for item in raw.get("external_reference_mappings", []))
        if references > self.max_references:
            raise PackResourceLimitError(f"pack {source} exceeds the external reference limit")

        manifest_fields = {item.name for item in fields(PackManifest)}
        manifest_values = {key: manifest_raw[key] for key in manifest_fields if key in manifest_raw}
        provenance = dict(manifest_values.get("provenance") or {})
        provenance.setdefault("content_hash", content_hash)
        provenance.setdefault("source", source)
        manifest_values["provenance"] = provenance
        manifest_values["lifecycle_state"] = lifecycle_state
        for key in ("subsectors", "protocol_profiles", "platform_profiles", "known_limitations", "external_reference_mappings", "required_core_guarantees"):
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
            content_hash=content_hash,
        )


class PackRegistry:
    def __init__(self, packs: list[Pack] | None = None, *, require_signature: bool = False, trust_policy: PackTrustPolicy | None = None, public_keys: dict[str, Any] | None = None, dependency_lock: DependencyLock | None = None) -> None:
        self._packs = {pack.pack_id: pack for pack in packs or []}
        self._disabled: set[str] = set()
        self._states = {pack.pack_id: pack.lifecycle_state for pack in packs or []}
        self._historical_hashes: dict[str, list[str]] = {}
        self.require_signature = require_signature
        self.trust_policy = trust_policy
        self.public_keys = dict(public_keys or {})
        self.dependency_lock = dependency_lock

    def register(self, pack: Pack) -> None:
        if pack.pack_id in self._packs:
            raise ValueError(f"pack already registered: {pack.pack_id}")
        self._packs[pack.pack_id] = pack
        self._states[pack.pack_id] = pack.lifecycle_state

    def transition(self, pack_id: str, target: PackLifecycleState) -> None:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        current = self._states[pack_id]
        allowed = {
            PackLifecycleState.DRAFT: {PackLifecycleState.PREVIEW, PackLifecycleState.DISABLED},
            PackLifecycleState.PREVIEW: {PackLifecycleState.ACTIVE, PackLifecycleState.DISABLED, PackLifecycleState.DRAFT},
            PackLifecycleState.ACTIVE: {PackLifecycleState.DEPRECATED, PackLifecycleState.DISABLED},
            PackLifecycleState.DEPRECATED: {PackLifecycleState.DISABLED},
            PackLifecycleState.DISABLED: {PackLifecycleState.PREVIEW, PackLifecycleState.DRAFT},
        }
        if target not in allowed[current]:
            raise PackCompatibilityError(f"invalid lifecycle transition {current.value} -> {target.value}")
        self._states[pack_id] = target

    def activate(self, pack_id: str, *, core_guarantees: Any | None = None) -> Pack:
        pack = self.get(pack_id, include_disabled=True)
        if not pack.content_hash or pack.manifest.provenance.get("content_hash") != pack.content_hash:
            raise PackCompatibilityError("pack integrity hash is not verifiable")
        if self.require_signature:
            envelope = parse_signature(pack.manifest.provenance.get("signature"))
            if envelope is None:
                raise PackCompatibilityError("pack signature is required by registry policy")
            if self.trust_policy is None:
                raise PackCompatibilityError("signature policy is required for production-capable activation")
            try:
                PackSignatureVerifier().verify(pack, envelope, public_keys=self.public_keys, policy=self.trust_policy, dependency_lock=self.dependency_lock)
            except PackSignatureError as exc:
                raise PackCompatibilityError(str(exc)) from exc
        if pack.manifest.required_core_guarantees:
            if core_guarantees is None:
                raise PackCompatibilityError("core guarantee registry is required for transactional pack activation")
            core_guarantees.require(pack.manifest.required_core_guarantees)
        if self._states[pack_id] == PackLifecycleState.DRAFT:
            self.transition(pack_id, PackLifecycleState.PREVIEW)
        self.transition(pack_id, PackLifecycleState.ACTIVE)
        self._disabled.discard(pack_id)
        return pack

    def disable(self, pack_id: str) -> None:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        self._disabled.add(pack_id)
        self._states[pack_id] = PackLifecycleState.DISABLED

    def enable(self, pack_id: str) -> None:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        self._disabled.discard(pack_id)
        if self._states[pack_id] == PackLifecycleState.DISABLED:
            self._states[pack_id] = PackLifecycleState.PREVIEW

    def remove(self, pack_id: str) -> None:
        pack = self.get(pack_id, include_disabled=True)
        self._historical_hashes.setdefault(pack_id, []).append(pack.content_hash)
        self._packs.pop(pack_id)
        self._states.pop(pack_id, None)
        self._disabled.discard(pack_id)

    def upgrade_impact(self, current: str, candidate: Pack) -> dict[str, list[str]]:
        old = self.get(current, include_disabled=True)
        return {
            "capabilities": sorted(set(item.capability_id for item in candidate.capabilities) ^ set(item.capability_id for item in old.capabilities)),
            "evaluation_scenarios": sorted(set(item.scenario_id for item in candidate.evaluation_scenarios) ^ set(item.scenario_id for item in old.evaluation_scenarios)),
            "protocol_profiles": sorted(set(str(item) for item in candidate.manifest.protocol_profiles) ^ set(str(item) for item in old.manifest.protocol_profiles)),
            "known_limitations": sorted(set(candidate.manifest.known_limitations) ^ set(old.manifest.known_limitations)),
            "trust": sorted(set(str(candidate.manifest.provenance.get(key, "")) for key in ("signature", "signing_key_id", "publisher", "dependency_lock_hash")) ^ set(str(old.manifest.provenance.get(key, "")) for key in ("signature", "signing_key_id", "publisher", "dependency_lock_hash"))),
            "required_core_guarantees": sorted(set(candidate.manifest.required_core_guarantees) ^ set(old.manifest.required_core_guarantees)),
        }

    def upgrade(self, pack: Pack) -> dict[str, list[str]]:
        current = self.get(pack.pack_id, include_disabled=True)
        impact = self.upgrade_impact(pack.pack_id, pack)
        self._historical_hashes.setdefault(pack.pack_id, []).append(current.content_hash)
        self._packs[pack.pack_id] = pack
        self._states[pack.pack_id] = pack.lifecycle_state
        return impact

    def validate_dependencies(self) -> None:
        graph: dict[str, set[str]] = {}
        for pack_id, pack in self._packs.items():
            required = pack.dependencies.get("packs", []) if isinstance(pack.dependencies, dict) else []
            if not isinstance(required, list):
                raise PackCompatibilityError(f"pack dependencies must be a list: {pack_id}")
            graph[pack_id] = {str(item) for item in required}
            missing = {item for item in graph[pack_id] if item not in self._packs and item != "agentnative.core"}
            if missing:
                raise PackCompatibilityError(f"missing pack dependencies for {pack_id}: {', '.join(sorted(missing))}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise PackCompatibilityError(f"circular pack dependency at {node}")
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph.get(node, ()):
                if dependency in graph:
                    visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for node in graph:
            visit(node)

    def get(self, pack_id: str, *, include_disabled: bool = False) -> Pack:
        if pack_id not in self._packs:
            raise KeyError(pack_id)
        if not include_disabled and pack_id in self._disabled:
            raise KeyError(f"pack is disabled: {pack_id}")
        return self._packs[pack_id]

    def list(self, *, include_disabled: bool = False) -> list[Pack]:
        return [pack for pack_id, pack in sorted(self._packs.items()) if include_disabled or pack_id not in self._disabled]

    def status(self) -> dict[str, str]:
        return {pack_id: ("DISABLED" if pack_id in self._disabled else self._states[pack_id].value.upper()) for pack_id in sorted(self._packs)}


def load_builtin_packs() -> PackRegistry:
    directory = Path(__file__).with_name("builtin")
    loader = PackLoader()
    return PackRegistry([loader.load_file(path) for path in sorted(directory.glob("*.yaml"))])


def _depth(value: Any, current: int = 0) -> int:
    if isinstance(value, dict):
        return max([current, *(_depth(item, current + 1) for item in value.values())])
    if isinstance(value, list):
        return max([current, *(_depth(item, current + 1) for item in value)])
    return current


__all__ = ["PackCompatibilityError", "PackLoader", "PackRegistry", "PackResourceLimitError", "load_builtin_packs", "pack_content_hash"]
