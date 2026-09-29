from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import fields
from datetime import datetime
from pathlib import Path

from agentnative import __version__
from agentnative.checks.catalog import CHECKS, CHECK_BY_ID
from agentnative.reporting.render import render_json, render_markdown, render_terminal
from agentnative.reporting.output import UnsafeReportError
from agentnative.scanner import scan
from agentnative.models import ExecutionStatus


def _policy_rules(document: object):
    from agentnative.policy import Decision, PolicyRule

    raw_rules = document if isinstance(document, list) else document.get("rules") if isinstance(document, dict) else None
    if not isinstance(raw_rules, list):
        raise ValueError("policy document must be a list or an object with a rules list")
    allowed = {item.name for item in fields(PolicyRule)}
    rules = []
    for raw in raw_rules:
        if not isinstance(raw, dict):
            raise ValueError("each policy rule must be an object")
        values = {key: value for key, value in raw.items() if key in allowed}
        if "policy_id" not in values:
            raise ValueError("each policy rule requires policy_id")
        if "decision" in values:
            values["decision"] = Decision(str(values["decision"]).upper())
        for key in ("effective_at", "expires_at"):
            if isinstance(values.get(key), str):
                values[key] = datetime.fromisoformat(values[key].replace("Z", "+00:00"))
        rules.append(PolicyRule(**values))
    return rules


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentnative", description="Evidence-backed passive Agent Native readiness checks")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="passively inspect a URL or local fixture")
    scan_parser.add_argument("target")
    scan_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    scan_parser.add_argument("--markdown", action="store_true", help="emit Markdown")
    scan_parser.add_argument("--verbose", action="store_true", help="reserved for additional diagnostic output")
    scan_parser.add_argument("--output", type=Path, help="write the selected report format to a file")

    for name in ("protocols", "capabilities"):
        protocol_parser = subparsers.add_parser(name, help="analyze a local protocol artifact")
        protocol_parser.add_argument("document")

    owner_parser = subparsers.add_parser("owner", help="inspect ownership verification workflows")
    owner_sub = owner_parser.add_subparsers(dest="owner_command")
    owner_sub.add_parser("status", help="show the status of a verification record")
    verify_parser = owner_sub.add_parser("verify", help="describe a verification target")
    verify_parser.add_argument("target")
    policy_parser = subparsers.add_parser("policy", help="evaluate deterministic participation policies")
    policy_sub = policy_parser.add_subparsers(dest="policy_command")
    lint_parser = policy_sub.add_parser("lint", help="lint a policy file")
    lint_parser.add_argument("policy_file")

    simulate_parser = subparsers.add_parser("simulate", help="run a controlled Phase 2C scenario")
    simulate_parser.add_argument("target", help="synthetic target label, or 'status'")
    simulate_parser.add_argument("run_id", nargs="?", help="run identifier for status lookup")
    simulate_parser.add_argument("--scenario", type=Path, help="scenario JSON file")
    simulate_parser.add_argument("--dry-run", action="store_true", help="evaluate controls without state-changing execution")
    simulate_parser.add_argument("--output", type=Path, help="write the sanitized simulation result")
    simulate_parser.add_argument("--receipt-output", type=Path, help="write the generated receipt")
    simulate_parser.add_argument("--trace-output", type=Path, help="write the structured trace")

    receipts_parser = subparsers.add_parser("receipts", help="verify simulation receipts")
    receipts_sub = receipts_parser.add_subparsers(dest="receipts_command", required=True)
    verify_receipt = receipts_sub.add_parser("verify", help="verify receipt integrity")
    verify_receipt.add_argument("receipt", type=Path)

    packs_parser = subparsers.add_parser("packs", help="inspect Agent Native v3 sector packs")
    packs_sub = packs_parser.add_subparsers(dest="packs_command", required=True)
    packs_sub.add_parser("list", help="list available sector packs")
    show_pack = packs_sub.add_parser("show", help="show one sector pack manifest and capabilities")
    show_pack.add_argument("pack_id")

    subparsers.add_parser("checks", help="list the deterministic check catalog")
    check_parser = subparsers.add_parser("check", help="show one check definition")
    check_parser.add_argument("check_id")
    subparsers.add_parser("version", help="show the scanner version")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "checks":
        for check in CHECKS:
            print(f"{check.id}\t{check.domain}\t{check.name}")
        return 0
    if args.command == "check":
        check = CHECK_BY_ID.get(args.check_id)
        if check is None:
            print(f"Unknown check: {args.check_id}", file=sys.stderr)
            return 2
        print(f"{check.id}: {check.name}")
        print(f"Domain: {check.domain}")
        print(f"Severity: {check.severity.value}")
        print(f"Description: {check.description}")
        print(f"Remediation: {check.remediation}")
        return 0
    if args.command in {"protocols", "capabilities"}:
        from agentnative.protocols import OpenAPIAdapter
        try:
            document = Path(args.document).read_text(encoding="utf-8")
            result = OpenAPIAdapter().parse(document, args.document)
        except (OSError, ValueError) as exc:
            print(f"Could not analyze protocol artifact: {exc}", file=sys.stderr)
            return 5
        payload = {
            "protocol_family": result.protocol_family,
            "protocol_version": result.protocol_version,
            "status": result.status,
            "capabilities": [{"name": item.name, "action_class": item.action_class.value, "side_effect": item.side_effect.value} for item in result.capabilities],
            "limitations": [item.__dict__ for item in result.limitations],
            "errors": result.errors,
            "error_details": [item.__dict__ for item in result.error_details],
        }
        print(json.dumps(payload, indent=2))
        return 0 if result.ok else 5
    if args.command == "owner":
        if args.owner_command == "verify":
            print(f"Ownership verification workflow configured for {args.target}; no active request was made.")
        else:
            print("No verification record supplied.")
        return 0
    if args.command == "policy":
        if args.policy_command == "lint":
            try:
                from agentnative.policy import PolicyLinter
                rules = _policy_rules(json.loads(Path(args.policy_file).read_text(encoding="utf-8")))
                findings = PolicyLinter().lint(rules)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                print(f"Policy file is not valid for v2 semantic linting: {exc}", file=sys.stderr)
                return 5
            print(json.dumps({"rule_count": len(rules), "findings": findings}, indent=2))
            return 1 if findings else 0
        return 0
    if args.command == "receipts":
        from agentnative.receipts import ReceiptEngine

        verification = ReceiptEngine().verify_file(args.receipt)
        print(json.dumps({"status": verification.status, "reason": verification.reason, "receipt_id": verification.receipt_id}, indent=2))
        return {"VALID": 0, "INVALID": 1, "UNSUPPORTED": 2}.get(verification.status, 2)
    if args.command == "packs":
        from agentnative.packs import load_builtin_packs

        registry = load_builtin_packs()
        if args.packs_command == "list":
            print(json.dumps({"packs": [{"pack_id": pack.pack_id, "sector": pack.manifest.sector, "version": pack.manifest.pack_version, "lifecycle_state": pack.lifecycle_state.value, "release_status": pack.manifest.release_status, "content_hash": pack.content_hash} for pack in registry.list()]}, indent=2))
            return 0
        try:
            pack = registry.get(args.pack_id)
        except KeyError:
            print(f"Unknown sector pack: {args.pack_id}", file=sys.stderr)
            return 2
        print(json.dumps({
            "pack_id": pack.pack_id,
            "manifest": {
                "pack_version": pack.manifest.pack_version,
                "sector": pack.manifest.sector,
                "subsectors": list(pack.manifest.subsectors),
                "core_version_requirement": pack.manifest.core_version_requirement,
                "release_status": pack.manifest.release_status,
                "lifecycle_state": pack.lifecycle_state.value,
                "namespace": pack.manifest.namespace,
                "required_core_guarantees": list(pack.manifest.required_core_guarantees),
                "content_hash": pack.content_hash,
                "provenance": dict(pack.manifest.provenance),
            },
            "capabilities": [
                {"capability_id": item.capability_id, "name": item.name, "group": item.group, "action_class": item.action_class.value, "side_effect": item.side_effect.value}
                for item in pack.capabilities
            ],
            "evaluation_scenarios": [
                {"scenario_id": item.scenario_id, "category": item.category.value, "expected_outcome": item.expected_outcome}
                for item in pack.evaluation_scenarios
            ],
            "known_limitations": list(pack.manifest.known_limitations),
        }, indent=2))
        return 0
    if args.command == "simulate":
        from agentnative.simulator import Scenario, Simulator
        from agentnative.receipts import ReceiptEngine

        run_directory = Path(".agentnative-runs")
        if args.target == "status":
            if not args.run_id or not re.fullmatch(r"run-[a-f0-9]{24}", args.run_id):
                print("Simulation run ID is invalid.", file=sys.stderr)
                return 2
            try:
                payload = json.loads((run_directory / f"{args.run_id}.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                print("Simulation run was not found.", file=sys.stderr)
                return 2
            print(json.dumps(payload, indent=2))
            return 0
        if args.scenario is None:
            print("--scenario is required for a simulation run.", file=sys.stderr)
            return 2
        try:
            raw_scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
            scenario = Scenario.from_dict(raw_scenario)
            result = Simulator().run(scenario, dry_run=args.dry_run)
            payload = result.to_dict()
            run_directory.mkdir(parents=True, exist_ok=True)
            (run_directory / f"{result.run_id}.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.output:
                args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if args.receipt_output and result.receipt:
                ReceiptEngine.write(result.receipt, args.receipt_output)
            if args.trace_output:
                args.trace_output.write_text(json.dumps(result.trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"Simulation scenario is not valid: {exc}", file=sys.stderr)
            return 5
        print(json.dumps(payload, indent=2))
        return 0 if result.status.value in {"DRY_RUN", "WOULD_ALLOW", "EXECUTED", "COMPENSATED"} else 3
    report = scan(args.target)
    try:
        if args.json or (args.output and args.output.suffix.lower() == ".json"):
            output = render_json(report)
        elif args.markdown or (args.output and args.output.suffix.lower() in {".md", ".markdown"}):
            output = render_markdown(report)
        else:
            output = render_terminal(report)
    except UnsafeReportError:
        print("Report blocked by output safety validation.", file=sys.stderr)
        return 6
    if args.output:
        try:
            args.output.write_text(output, encoding="utf-8")
        except OSError as exc:
            print(f"Could not write report: {exc}", file=sys.stderr)
            return 5
    else:
        print(output, end="" if output.endswith("\n") else "\n")
    return {
        ExecutionStatus.COMPLETED: 0,
        ExecutionStatus.POLICY_BLOCKED: 3,
        ExecutionStatus.ACQUISITION_ERROR: 4,
        ExecutionStatus.INTERNAL_ERROR: 5,
    }.get(report.execution_status, 5)
