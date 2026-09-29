"""Strict, dependency-light validation for the Retail product workspace.

The product intentionally keeps this contract small and explicit.  A workspace is
user input, not a trusted internal object, so domain construction happens only
after this module has checked the complete nested shape.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


CURRENT_WORKSPACE_VERSION = "1.1"
SUPPORTED_WORKSPACE_VERSIONS = {"1.0", CURRENT_WORKSPACE_VERSION}
CANONICALIZATION_VERSION = "retail-workspace-c14n-1"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    json_path: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "json_path": self.json_path, "message": self.message, "remediation": self.remediation}


class WorkspaceValidationError(ValueError):
    """Stable public error contract for malformed Retail workspaces."""

    def __init__(self, issues: list[ValidationIssue] | ValidationIssue | str):
        if isinstance(issues, str):
            issues = [ValidationIssue("INVALID_WORKSPACE", "$", issues, "Fix the workspace and run retail validate again.")]
        elif isinstance(issues, ValidationIssue):
            issues = [issues]
        self.issues = tuple(issues)
        super().__init__(self.issues[0].message if self.issues else "workspace is invalid")

    @property
    def code(self) -> str:
        return self.issues[0].code if self.issues else "INVALID_WORKSPACE"

    def to_dict(self) -> dict[str, Any]:
        return {"status": "INVALID_PROJECT", "error_code": self.code, "errors": [item.to_dict() for item in self.issues]}


def _issue(code: str, path: str, message: str, remediation: str) -> ValidationIssue:
    return ValidationIssue(code, path, message, remediation)


def migrate_workspace(raw: dict[str, Any]) -> dict[str, Any]:
    """Migrate the supported 1.0 shape without mutating caller-owned data."""
    import copy

    version = str(raw.get("project_version", ""))
    if version not in SUPPORTED_WORKSPACE_VERSIONS:
        raise WorkspaceValidationError(_issue("UNSUPPORTED_WORKSPACE_VERSION", "$.project_version", f"workspace version {version!r} is unsupported", "Migrate to workspace version 1.1 before loading it."))
    migrated = copy.deepcopy(raw)
    if version == "1.0":
        migrated["project_version"] = CURRENT_WORKSPACE_VERSION
        migrated.setdefault("extensions", {})
        migrated.setdefault("schema_migrations", ["1.0->1.1"])
    return migrated


def _type(issues: list[ValidationIssue], value: Any, expected: type | tuple[type, ...], path: str) -> bool:
    numeric_expected = expected in {int, float} if isinstance(expected, type) else any(item in {int, float} for item in expected)
    if not isinstance(value, expected) or isinstance(value, bool) and numeric_expected:
        issues.append(_issue("TYPE_ERROR", path, f"expected {getattr(expected, '__name__', 'a valid type')}", "Use the documented workspace type."))
        return False
    return True


def _id(issues: list[ValidationIssue], value: Any, path: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        issues.append(_issue("INVALID_ID", path, "identifier must be a nonempty stable namespaced ID", "Use letters, digits, and . : / _ - only."))


def _unique_ids(issues: list[ValidationIssue], records: Any, path: str, key: str) -> None:
    if not isinstance(records, list):
        return
    seen: set[str] = set()
    for index, record in enumerate(records):
        item_path = f"{path}[{index}]"
        if not isinstance(record, dict):
            issues.append(_issue("TYPE_ERROR", item_path, "expected an object", "Replace the list item with an object."))
            continue
        if key not in record:
            issues.append(_issue("MISSING_FIELD", f"{item_path}.{key}", f"missing {key}", f"Add a stable {key}."))
            continue
        _id(issues, record[key], f"{item_path}.{key}")
        if record[key] in seen:
            issues.append(_issue("DUPLICATE_ID", f"{item_path}.{key}", f"duplicate {key}: {record[key]}", "Make every identifier unique within this collection."))
        seen.add(str(record[key]))


def _guard_yaml_shape(value: Any, *, max_depth: int = 32, max_nodes: int = 10_000) -> None:
    seen: set[int] = set()
    nodes = 0

    def walk(item: Any, path: str, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > max_nodes:
            raise WorkspaceValidationError(_issue("RESOURCE_LIMIT", path, "workspace exceeds the node limit", "Reduce the document size and remove unnecessary YAML aliases."))
        if depth > max_depth:
            raise WorkspaceValidationError(_issue("RESOURCE_LIMIT", path, "workspace nesting exceeds the safety limit", "Flatten deeply nested YAML and retry."))
        if isinstance(item, (dict, list)):
            identity = id(item)
            if identity in seen:
                raise WorkspaceValidationError(_issue("YAML_ALIAS_CYCLE", path, "cyclic or repeated YAML alias is not supported", "Expand the alias into explicit bounded data."))
            seen.add(identity)
            iterator = item.items() if isinstance(item, dict) else enumerate(item)
            for key, child in iterator:
                walk(child, f"{path}.{key}" if isinstance(item, dict) else f"{path}[{key}]", depth + 1)

    walk(value, "$", 0)


def validate_workspace_shape(raw: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise WorkspaceValidationError("project.yaml must contain an object")
    _guard_yaml_shape(raw)
    raw = migrate_workspace(raw)
    issues: list[ValidationIssue] = []
    required = {"project_id", "project_version", "business_id", "tenant_id", "name", "sector_pack", "pack_version", "environment", "business_profile", "platform_inventory", "capability_inventory", "protocol_profiles", "priority_journeys", "evidence_sources", "policy_profile", "simulation_profile"}
    allowed = required | {"created_at", "updated_at", "extensions", "schema_migrations"}
    for key in sorted(set(raw) - allowed):
        issues.append(_issue("UNKNOWN_FIELD", f"$.{key}", f"unknown workspace field: {key}", "Remove it or place it under the versioned extensions namespace."))
    for key in sorted(required - set(raw)):
        issues.append(_issue("MISSING_FIELD", f"$.{key}", f"missing required field: {key}", "Add the field from the Retail workspace schema."))
    for key in ("project_id", "business_id", "tenant_id", "name", "sector_pack", "pack_version", "environment"):
        if key in raw:
            _id(issues, raw[key], f"$.{key}") if key not in {"name"} else _type(issues, raw[key], str, f"$.{key}")
    if raw.get("project_version") not in SUPPORTED_WORKSPACE_VERSIONS and raw.get("project_version") != CURRENT_WORKSPACE_VERSION:
        issues.append(_issue("UNSUPPORTED_WORKSPACE_VERSION", "$.project_version", f"workspace version {raw.get('project_version')!r} is unsupported", "Migrate to workspace version 1.1."))
    if raw.get("sector_pack") != "sector.retail":
        issues.append(_issue("UNSUPPORTED_PACK", "$.sector_pack", "sector_pack must be sector.retail", "Use the Retail pack or select a supported product."))
    if raw.get("environment") not in {"SANDBOX", "STAGING", "PRODUCTION_READ_ONLY", "PRODUCTION_ACTIVE"}:
        issues.append(_issue("INVALID_ENUM", "$.environment", "environment is unsupported", "Use SANDBOX, STAGING, PRODUCTION_READ_ONLY, or PRODUCTION_ACTIVE."))

    profile = raw.get("business_profile")
    profile_fields = {"business_model": str, "business_size": str, "technical_capacity": str, "api_maturity": str, "existing_platforms": list, "data_sensitivity": str, "regulatory_sensitivity": str, "reversibility": str, "customer_identity_requirement": str, "payment_requirement": str, "real_time_inventory_requirement": bool, "human_staff_availability": str, "agent_channel_priority": str, "expected_agent_volume": int, "margin_per_action": (int, float), "protocol_platform_fee_per_action": (int, float), "connector_cost_per_action": (int, float), "inference_cost_per_action": (int, float), "human_handoff_cost_per_action": (int, float), "cost_ceiling_per_action": (int, float)}
    if _type(issues, profile, dict, "$.business_profile"):
        for key, expected in profile_fields.items():
            if key not in profile:
                issues.append(_issue("MISSING_FIELD", f"$.business_profile.{key}", f"missing business profile field: {key}", "Provide the complete typed business profile."))
            elif not _type(issues, profile[key], expected, f"$.business_profile.{key}"):
                continue
            elif key not in {"existing_platforms", "real_time_inventory_requirement"} and isinstance(profile[key], (int, float)) and (not math.isfinite(float(profile[key])) or float(profile[key]) < 0):
                issues.append(_issue("INVALID_NUMBER", f"$.business_profile.{key}", "money and volume values must be finite and nonnegative", "Use a finite nonnegative number."))
        if isinstance(profile.get("existing_platforms"), list) and not all(isinstance(item, str) and item.strip() for item in profile["existing_platforms"]):
            issues.append(_issue("INVALID_VALUE", "$.business_profile.existing_platforms", "platform identifiers must be nonempty strings", "Use stable platform identifiers."))

    _unique_ids(issues, raw.get("platform_inventory"), "$.platform_inventory", "platform_id")
    capabilities = raw.get("capability_inventory")
    _unique_ids(issues, capabilities, "$.capability_inventory", "capability_id")
    valid_states = {"DECLARED", "OBSERVED", "TESTED", "EXECUTABLE_IN_SIMULATION", "EXECUTABLE_IN_SANDBOX", "UNAVAILABLE", "UNKNOWN"}
    if isinstance(capabilities, list):
        for index, item in enumerate(capabilities):
            if not isinstance(item, dict):
                continue
            state = item.get("state")
            if state not in valid_states:
                issues.append(_issue("INVALID_ENUM", f"$.capability_inventory[{index}].state", "unknown capability state", "Use a documented CapabilityState."))
            if state in {"TESTED", "EXECUTABLE_IN_SIMULATION", "EXECUTABLE_IN_SANDBOX"}:
                refs = item.get("evidence_refs")
                if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref for ref in refs):
                    issues.append(_issue("EVIDENCE_REQUIRED", f"$.capability_inventory[{index}].evidence_refs", "readiness-bearing capability states require evidence_refs", "Attach resolvable test or sandbox evidence."))

    _unique_ids(issues, raw.get("protocol_profiles"), "$.protocol_profiles", "profile_id")
    if isinstance(raw.get("protocol_profiles"), list):
        for index, item in enumerate(raw["protocol_profiles"]):
            if not isinstance(item, dict):
                continue
            for key in ("protocol_name", "protocol_version", "profile_version", "source_hash"):
                if not isinstance(item.get(key), str) or not item[key].strip():
                    issues.append(_issue("MISSING_FIELD", f"$.protocol_profiles[{index}].{key}", f"protocol profile requires {key}", "Provide the pinned profile metadata and source hash."))

    evidence = raw.get("evidence_sources")
    _unique_ids(issues, evidence, "$.evidence_sources", "evidence_id") if isinstance(evidence, list) and any(isinstance(item, dict) and "evidence_id" in item for item in evidence) else None
    evidence_refs: set[str] = set()
    now = now or datetime.now(timezone.utc)
    if not isinstance(evidence, list):
        issues.append(_issue("TYPE_ERROR", "$.evidence_sources", "evidence_sources must be a list", "Provide evidence records."))
    else:
        for index, item in enumerate(evidence):
            path = f"$.evidence_sources[{index}]"
            if not isinstance(item, dict):
                issues.append(_issue("TYPE_ERROR", path, "evidence source must be an object", "Provide a typed evidence record."))
                continue
            for key in ("field_name", "source_ref", "observed_at", "confidence", "state"):
                if key not in item:
                    issues.append(_issue("MISSING_FIELD", f"{path}.{key}", f"missing evidence field: {key}", "Provide provenance, timestamp, confidence, and state."))
            evidence_refs.update(str(value) for value in (item.get("evidence_id"), item.get("source_ref")) if value)
            try:
                observed = datetime.fromisoformat(str(item.get("observed_at", "")).replace("Z", "+00:00"))
                if observed.tzinfo is None:
                    raise ValueError
                if observed > now + timedelta(days=2):
                    issues.append(_issue("FUTURE_EVIDENCE", f"{path}.observed_at", "evidence timestamp is beyond the allowed clock skew", "Use the observation time from the collector."))
            except (TypeError, ValueError):
                issues.append(_issue("INVALID_TIMESTAMP", f"{path}.observed_at", "evidence timestamp must be timezone-aware ISO-8601", "Use a timestamp ending in Z or with an explicit offset."))
            try:
                confidence = float(item.get("confidence"))
                if not math.isfinite(confidence) or not 0 <= confidence <= 1:
                    raise ValueError
            except (TypeError, ValueError):
                issues.append(_issue("INVALID_CONFIDENCE", f"{path}.confidence", "confidence must be finite and in [0, 1]", "Use a numeric confidence between 0 and 1."))
            if item.get("state") not in {"KNOWN_TRUE", "KNOWN_FALSE", "UNKNOWN", "UNVERIFIED", "CONFLICTING", "STALE"}:
                issues.append(_issue("INVALID_ENUM", f"{path}.state", "unknown evidence state", "Use a documented EvidenceState."))

    journeys = raw.get("priority_journeys")
    if not isinstance(journeys, list) or not journeys or not all(isinstance(item, str) and item for item in journeys):
        issues.append(_issue("INVALID_VALUE", "$.priority_journeys", "priority_journeys must be a nonempty list of IDs", "Select journeys from the Retail journey registry."))
    elif len(set(journeys)) != len(journeys):
        issues.append(_issue("DUPLICATE_ID", "$.priority_journeys", "priority journeys must be unique", "List each priority journey once."))

    policy = raw.get("policy_profile")
    if _type(issues, policy, dict, "$.policy_profile"):
        if policy.get("risk_tolerance") not in {"low", "bounded", "medium", "high"}:
            issues.append(_issue("INVALID_ENUM", "$.policy_profile.risk_tolerance", "risk_tolerance is unsupported", "Use low, bounded, medium, or high."))
        if not isinstance(policy.get("require_confirmation_for"), list):
            issues.append(_issue("TYPE_ERROR", "$.policy_profile.require_confirmation_for", "require_confirmation_for must be a list", "List capability IDs requiring confirmation."))
        if not isinstance(policy.get("human_handoff_enabled"), bool):
            issues.append(_issue("TYPE_ERROR", "$.policy_profile.human_handoff_enabled", "human_handoff_enabled must be boolean", "Set an explicit handoff policy."))

    simulation = raw.get("simulation_profile")
    if _type(issues, simulation, dict, "$.simulation_profile"):
        for key in ("scenario_version", "product_id", "variant_id", "currency"):
            if not isinstance(simulation.get(key), str) or not simulation[key].strip():
                issues.append(_issue("MISSING_FIELD", f"$.simulation_profile.{key}", f"missing simulation field: {key}", "Provide deterministic simulation metadata."))
        if not _CURRENCY.fullmatch(str(simulation.get("currency", ""))):
            issues.append(_issue("INVALID_CURRENCY", "$.simulation_profile.currency", "currency must be an ISO-4217 uppercase code", "Use a three-letter uppercase currency code."))
        for key in ("price", "inventory"):
            value = simulation.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or float(value) < 0 or (key == "inventory" and int(value) != value):
                issues.append(_issue("INVALID_NUMBER", f"$.simulation_profile.{key}", f"simulation {key} must be finite and nonnegative", "Use a valid price or nonnegative integer inventory."))

    if isinstance(evidence, list) and isinstance(capabilities, list):
        for index, item in enumerate(capabilities):
            if isinstance(item, dict) and item.get("state") in {"TESTED", "EXECUTABLE_IN_SIMULATION", "EXECUTABLE_IN_SANDBOX"}:
                for ref in item.get("evidence_refs", []):
                    if ref not in evidence_refs:
                        issues.append(_issue("UNRESOLVABLE_EVIDENCE", f"$.capability_inventory[{index}].evidence_refs", f"evidence reference {ref!r} does not resolve", "Add the evidence record or downgrade the capability state."))
    if issues:
        raise WorkspaceValidationError(issues)
    return raw


__all__ = ["CANONICALIZATION_VERSION", "CURRENT_WORKSPACE_VERSION", "SUPPORTED_WORKSPACE_VERSIONS", "ValidationIssue", "WorkspaceValidationError", "migrate_workspace", "validate_workspace_shape"]
