from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse
from typing import Any, Protocol


class SideEffectMode(StrEnum):
    READ_ONLY = "READ_ONLY"
    SIMULATED = "SIMULATED"
    SANDBOX_MUTATION = "SANDBOX_MUTATION"
    PRODUCTION_MUTATION = "PRODUCTION_MUTATION"


class ConnectorResultState(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    DENIED = "DENIED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_TERMINAL = "FAILED_TERMINAL"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"
    PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class ConnectorBinding:
    connector_id: str
    connector_version: str
    tenant_id: str
    business_id: str
    environment: str
    endpoint_allowlist: tuple[str, ...]
    credential_reference: str
    credential_class: str
    permitted_capabilities: tuple[str, ...]
    side_effect_mode: SideEffectMode = SideEffectMode.READ_ONLY
    require_https: bool = True


class ConnectorPolicyError(ValueError):
    pass


class SecretProvider(Protocol):
    def resolve(self, credential_reference: str, *, tenant_id: str, environment: str) -> str: ...


class ConnectorContract(Protocol):
    def discover_capabilities(self) -> tuple[str, ...]: ...
    def test_connection(self) -> bool: ...
    def read_configuration(self) -> dict[str, Any]: ...
    def read_resource(self, resource_id: str) -> dict[str, Any]: ...
    def prepare_action(self, action: str, payload: dict[str, Any]) -> Any: ...
    def execute_action(self, action: str, payload: dict[str, Any]) -> Any: ...
    def verify_action(self, action: str, reference: str) -> Any: ...
    def compensate_action(self, action: str, reference: str) -> Any: ...
    def normalize_result(self, result: Any) -> ConnectorResultState: ...


class ConnectorEnvironmentPolicy:
    def validate(self, binding: ConnectorBinding, *, endpoint: str, transaction_environment: str, mutation: bool = False, connector_version: str | None = None, allowed_versions: tuple[str, ...] = ()) -> None:
        parsed = urlparse(endpoint)
        if parsed.username or parsed.password:
            raise ConnectorPolicyError("embedded credentials are forbidden in connector endpoints")
        if binding.require_https and parsed.scheme != "https" and not (parsed.hostname in {"localhost", "127.0.0.1", "::1"} and parsed.scheme == "http"):
            raise ConnectorPolicyError("connector endpoint must use HTTPS")
        if not parsed.hostname or not self._allowlisted(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80), binding.endpoint_allowlist):
            raise ConnectorPolicyError("connector endpoint is not allowlisted")
        if binding.environment != transaction_environment:
            raise ConnectorPolicyError("connector environment does not match transaction environment")
        if binding.side_effect_mode == SideEffectMode.READ_ONLY and mutation:
            raise ConnectorPolicyError("read-only connector cannot perform mutations")
        if binding.side_effect_mode == SideEffectMode.SIMULATED and mutation:
            raise ConnectorPolicyError("simulated connector cannot perform downstream mutations")
        if binding.environment.startswith("PRODUCTION") and binding.side_effect_mode != SideEffectMode.PRODUCTION_MUTATION:
            raise ConnectorPolicyError("production connector requires an explicit production mutation mode")
        if connector_version and allowed_versions and connector_version not in allowed_versions:
            raise ConnectorPolicyError("connector version is not allowed by the active pack lock")

    @staticmethod
    def _allowlisted(host: str, port: int, allowlist: tuple[str, ...]) -> bool:
        host = host.lower().rstrip(".")
        try:
            address = ipaddress.ip_address(host)
            if address.is_loopback or address.is_link_local or address.is_private:
                return any(item in {host, f"{host}:{port}"} for item in allowlist)
        except ValueError:
            pass
        return any(item in {host, f"{host}:{port}"} or (item.startswith("*.") and host.endswith(item[1:])) for item in allowlist)


class InMemorySecretProvider:
    """Test provider that never serializes secret values into a binding or result."""

    def __init__(self, values: dict[str, str]) -> None:
        self._values = dict(values)

    def resolve(self, credential_reference: str, *, tenant_id: str, environment: str) -> str:
        if credential_reference not in self._values:
            raise ConnectorPolicyError("credential reference is unavailable")
        return self._values[credential_reference]


class SyntheticMerchantConnector:
    """Deterministic local connector used to exercise the real boundary without I/O."""

    def __init__(self, binding: ConnectorBinding, *, endpoint: str, policy: ConnectorEnvironmentPolicy | None = None) -> None:
        self.binding = binding
        self.endpoint = endpoint
        self.policy = policy or ConnectorEnvironmentPolicy()
        self._resources: dict[str, dict[str, Any]] = {}

    def discover_capabilities(self) -> tuple[str, ...]:
        return self.binding.permitted_capabilities

    def test_connection(self) -> bool:
        self.policy.validate(self.binding, endpoint=self.endpoint, transaction_environment=self.binding.environment)
        return True

    def read_configuration(self) -> dict[str, Any]:
        self.test_connection()
        return {"connector_id": self.binding.connector_id, "environment": self.binding.environment, "side_effect_mode": self.binding.side_effect_mode.value}

    def read_resource(self, resource_id: str) -> dict[str, Any]:
        self.test_connection()
        return dict(self._resources.get(resource_id, {}))

    def prepare_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        if action not in self.binding.permitted_capabilities:
            raise ConnectorPolicyError("connector capability is not permitted")
        return {"action": action, "payload": dict(payload)}

    def execute_action(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.policy.validate(self.binding, endpoint=self.endpoint, transaction_environment=self.binding.environment, mutation=True)
        prepared = self.prepare_action(action, payload)
        reference = str(payload.get("reference") or f"synthetic:{len(self._resources) + 1}")
        result = {"state": ConnectorResultState.SUCCEEDED.value, "reference": reference, "action": prepared["action"]}
        self._resources[reference] = result
        return result

    def verify_action(self, action: str, reference: str) -> dict[str, Any]:
        self.test_connection()
        return dict(self._resources.get(reference, {"state": ConnectorResultState.FAILED_TERMINAL.value, "reference": reference}))

    def compensate_action(self, action: str, reference: str) -> dict[str, Any]:
        self.policy.validate(self.binding, endpoint=self.endpoint, transaction_environment=self.binding.environment, mutation=True)
        if reference not in self._resources:
            return {"state": ConnectorResultState.FAILED_TERMINAL.value, "reference": reference}
        self._resources[reference]["state"] = "COMPENSATED"
        return dict(self._resources[reference])

    def normalize_result(self, result: Any) -> ConnectorResultState:
        if not isinstance(result, dict):
            return ConnectorResultState.FAILED_TERMINAL
        try:
            return ConnectorResultState(str(result.get("state", "FAILED_TERMINAL")))
        except ValueError:
            return ConnectorResultState.FAILED_TERMINAL


__all__ = ["ConnectorBinding", "ConnectorContract", "ConnectorEnvironmentPolicy", "ConnectorPolicyError", "ConnectorResultState", "InMemorySecretProvider", "SecretProvider", "SideEffectMode", "SyntheticMerchantConnector"]
