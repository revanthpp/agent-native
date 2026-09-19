from __future__ import annotations

import uuid
from pathlib import Path

from agentnative import CHECK_SET_VERSION, __version__
from agentnative.acquisition.fetcher import AcquisitionError, FixtureFetcher, SafeFetcher
from agentnative.checks.catalog import CHECKS
from agentnative.checks.engine import run_checks
from agentnative.discovery.discover import discover
from agentnative.models import CheckResult, ExecutionStatus, Limitation, ResultStatus, ScanReport, Target, utc_now
from agentnative.security.policy import NetworkPolicy
from agentnative.security.policy import UnsafeTargetError


def scan(target_value: str, *, policy: NetworkPolicy | None = None) -> ScanReport:
    scan_id = str(uuid.uuid4())
    started = utc_now()
    target_text = str(target_value)
    kind = "local" if Path(target_text).exists() else "network"
    target = Target(raw=target_text, canonical=target_text, kind=kind)
    fetcher = FixtureFetcher() if kind == "local" else SafeFetcher(policy)
    execution_status = ExecutionStatus.COMPLETED
    try:
        surface = discover(target_text, fetcher)
        results = run_checks(surface, target, scan_id)
        limitations = surface.limitations
        artifacts = surface.artifacts
        if any(result.status == ResultStatus.ERROR for result in results):
            execution_status = ExecutionStatus.INTERNAL_ERROR
            limitations = [*limitations, Limitation("CHECK_EXECUTION_FAILED", None, "One or more deterministic checks failed internally; inspect ERROR results.")]
    except UnsafeTargetError as exc:
        execution_status = ExecutionStatus.POLICY_BLOCKED
        results = [CheckResult(check, ResultStatus.ERROR, f"Scan blocked by target policy: {exc}", check.remediation, 0.0, []) for check in CHECKS]
        limitations = [Limitation("TARGET_POLICY_BLOCKED", target_text, type(exc).__name__)]
        artifacts = []
    except AcquisitionError as exc:
        execution_status = ExecutionStatus.ACQUISITION_ERROR
        results = [CheckResult(check, ResultStatus.ERROR, f"Scan could not acquire target safely: {exc}", check.remediation, 0.0, []) for check in CHECKS]
        limitations = [Limitation("TARGET_ACQUISITION_FAILED", target_text, type(exc).__name__)]
        artifacts = []
    except Exception as exc:
        execution_status = ExecutionStatus.INTERNAL_ERROR
        results = [CheckResult(check, ResultStatus.ERROR, f"Internal scanner failure: {type(exc).__name__}", check.remediation, 0.0, []) for check in CHECKS]
        limitations = [Limitation("INTERNAL_SCANNER_FAILURE", target_text, type(exc).__name__)]
        artifacts = []
    return ScanReport(scan_id, target, started, utc_now(), __version__, CHECK_SET_VERSION, results, artifacts, limitations, execution_status)
