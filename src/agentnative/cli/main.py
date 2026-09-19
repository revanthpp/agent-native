from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agentnative import __version__
from agentnative.checks.catalog import CHECKS, CHECK_BY_ID
from agentnative.reporting.render import render_json, render_markdown, render_terminal
from agentnative.reporting.output import UnsafeReportError
from agentnative.scanner import scan
from agentnative.models import ExecutionStatus


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
