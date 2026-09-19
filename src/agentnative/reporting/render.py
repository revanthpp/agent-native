from __future__ import annotations

import json

from agentnative.models import PublicReport, ResultStatus, ScanReport
from agentnative.reporting.output import validate_output
from agentnative.reporting.safe import SafeReportBuilder
from agentnative.security.sanitize import Sanitizer


def _safe(report: ScanReport) -> PublicReport:
    return SafeReportBuilder().build(report)


def render_json(report: ScanReport) -> str:
    output = json.dumps(_safe(report).to_dict(), indent=2, sort_keys=True) + "\n"
    validate_output(output)
    return output


def render_markdown(report: ScanReport) -> str:
    report = _safe(report)
    lines = [
        "# Agent Native Readiness Profile",
        "",
        f"Target: `{report.target.canonical}`  ",
        f"Scan ID: `{report.scan_id}`  ",
        f"Agent Native: `{report.version}`  ",
        f"Check set: `{report.check_set_version}`  ",
        "",
        "This is a passive, evidence-backed profile. `NOT_OBSERVED` means the scanner could not establish a capability from the bounded public surface; it is not proof of absence.",
        "",
        "## Summary",
        "",
    ]
    summary = report.summary
    lines.append(" | ".join(f"{key}: {summary[key]}" for key in ResultStatus))
    lines += ["", "## Findings", "", "| ID | Domain | Status | Severity | Explanation |", "|---|---|---|---|---|"]
    for result in report.results:
        explanation = result.explanation.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {result.check.id} | {result.check.domain} | {result.status.value} | {result.check.severity.value} | {explanation} |")
    lines += ["", "## Evidence", ""]
    for result in report.results:
        for evidence in result.evidence:
            lines += [
                f"### {result.check.id} {result.check.name}",
                "",
                f"- Source: `{evidence.source_uri}`",
                f"- Artifact: `{evidence.artifact_type}`",
                f"- Evidence ID: `{evidence.evidence_id}`",
                f"- Observation: {evidence.observation}",
                f"- Confidence: {evidence.confidence:.2f}",
                "",
            ]
    if report.limitations:
        lines += ["## Limitations", ""]
        lines.extend(f"- {item}" for item in report.limitations)
        lines.append("")
    output = "\n".join(lines)
    validate_output(output)
    return output


def render_terminal(report: ScanReport) -> str:
    report = _safe(report)
    sanitizer = Sanitizer()
    summary = report.summary
    lines = [
        "Agent Native v1.0.0 | passive readiness profile",
        f"Target: {sanitizer.terminal(report.target.canonical)}",
        f"Execution: {report.execution_status.value}",
        "",
        "Summary: " + "  ".join(f"{status.value}={summary[status.value]}" for status in ResultStatus),
        "",
    ]
    for result in report.results:
        lines.append(sanitizer.terminal(f"{result.status.value:<14} {result.check.id}  {result.check.name} — {result.explanation}"))
    if report.limitations:
        lines += ["", "Limitations:"]
        lines.extend(f"- {sanitizer.terminal(str(item))}" for item in report.limitations)
    lines += ["", "Evidence is preserved per finding in JSON/Markdown output. NOT_OBSERVED is not proof of absence."]
    output = "\n".join(lines)
    validate_output(output)
    return output
