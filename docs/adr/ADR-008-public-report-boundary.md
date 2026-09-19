# ADR-008: Sanitized public report boundary

## Status

Accepted for v0.1 remediation.

## Context

The first implementation used the internal artifact model as the JSON report
shape. That model intentionally contains acquired content and headers for
parsing and evidence checks. Serializing it made a public report a possible
secret and internal-data exfiltration channel.

## Decision

Keep raw `Artifact` objects internal to acquisition, discovery, parsing, and
checks. Expose only `ArtifactSummary` through `ScanReport.public_projection()`.
All renderers validate evidence before producing output. Evidence must resolve
to an acquired artifact and match its URI, type, and content hash.

## Consequences

- Public reports retain auditability without returning raw target payloads.
- Evidence can be independently checked for provenance integrity.
- New report fields must be deliberately added to the public projection.
- Internal parsers can retain content without silently widening the output
  contract.

## Verification

`tests/security/test_report_integrity.py` checks payload exclusion and tamper
rejection. The remediation regression suite covers a secret-bearing artifact,
and the renderers all use the same validation gate.
