"""Fail-closed verifier for the Phase 3B Gate 2 evidence manifest.

The verifier is deliberately independent of the builder's result-producing code.
It validates the manifest, local artifact bytes, Git ancestry, and (unless
``--offline`` is explicitly requested) the GitHub Actions run and uploaded
artifact that produced the evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


GENERATOR_VERSION = "gate2-verifier-1.0"
REPOSITORY = "revanthpp/agent-native"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACT_ROLES = (
    "closure_build_report",
    "requirements_traceability",
    "wheel",
    "structured_test_result",
    "phase2b_mutation_result",
    "phase2c_mutation_result",
    "phase3_mutation_result",
    "wheel_smoke_result",
)
REQUIRED_COMMAND_IDS = (
    "baseline_tests",
    "evidence_tamper_matrix",
    "phase3_mutations",
    "wheel_smoke",
    "manifest_generation",
    "manifest_local_verification",
)


@dataclass(frozen=True)
class VerificationError:
    error_code: str
    json_path: str
    message: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return {
            "error_code": self.error_code,
            "json_path": self.json_path,
            "message": self.message,
            "remediation": self.remediation,
        }


def _error(errors: list[VerificationError], code: str, path: str, message: str, remediation: str) -> None:
    errors.append(VerificationError(code, path, message, remediation))


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _canonical_output_digest(output: Any) -> str:
    encoded = json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _digest_bytes(encoded)


def _validate_shape(manifest: Any, errors: list[VerificationError]) -> None:
    if not isinstance(manifest, dict):
        _error(errors, "MANIFEST_TYPE", "$", "manifest must be a JSON object", "Regenerate the Gate 2 manifest.")
        return
    required = {
        "manifest_version", "status", "repository", "source_commit_sha", "reviewed_commit_sha",
        "evidence_commit_sha", "generated_at", "generator_version", "ci", "artifacts", "commands", "results",
    }
    for key in sorted(required - set(manifest)):
        _error(errors, "MISSING_FIELD", f"$.{key}", "required manifest field is missing", "Regenerate the manifest with the current generator.")
    for key in sorted(set(manifest) - required):
        _error(errors, "UNKNOWN_FIELD", f"$.{key}", "unknown manifest field is not permitted", "Remove the field or update the versioned schema deliberately.")
    if set(manifest) - required:
        return
    if manifest.get("manifest_version") != "phase3b-gate2-1":
        _error(errors, "MANIFEST_VERSION", "$.manifest_version", "unsupported manifest_version", "Use phase3b-gate2-1.")
    if manifest.get("status") != "BUILDER_EVIDENCE_ONLY":
        _error(errors, "STATUS_UNSUPPORTED", "$.status", "builder evidence must remain BUILDER_EVIDENCE_ONLY", "Do not self-promote; regenerate builder evidence.")
    if manifest.get("repository") != REPOSITORY:
        _error(errors, "REPOSITORY_MISMATCH", "$.repository", "manifest repository does not match the approved repository", f"Set repository to {REPOSITORY}.")
    for field in ("source_commit_sha", "reviewed_commit_sha", "evidence_commit_sha"):
        value = manifest.get(field)
        if not isinstance(value, str) or not SHA_RE.fullmatch(value):
            _error(errors, "INVALID_COMMIT_SHA", f"$.{field}", "commit identifier must be a full lowercase 40-character SHA", "Use git rev-parse to record the full commit SHA.")
    if _parse_timestamp(manifest.get("generated_at")) is None:
        _error(errors, "INVALID_TIMESTAMP", "$.generated_at", "timestamp must be an ISO-8601 value", "Record a UTC ISO-8601 timestamp.")
    if not isinstance(manifest.get("generator_version"), str) or not manifest.get("generator_version"):
        _error(errors, "INVALID_TYPE", "$.generator_version", "generator_version must be a non-empty string", "Regenerate the manifest.")
    if not isinstance(manifest.get("ci"), dict):
        _error(errors, "INVALID_TYPE", "$.ci", "ci must be an object", "Record the complete GitHub run identity.")
    if not isinstance(manifest.get("artifacts"), list):
        _error(errors, "INVALID_TYPE", "$.artifacts", "artifacts must be an array", "Record artifact metadata for every required role.")
    if not isinstance(manifest.get("commands"), list):
        _error(errors, "INVALID_TYPE", "$.commands", "commands must be an array", "Record every required command result.")
    if not isinstance(manifest.get("results"), dict):
        _error(errors, "INVALID_TYPE", "$.results", "results must be an object", "Record structured Gate 2 result counts.")


def _validate_schema_contract(root: Path, errors: list[VerificationError]) -> None:
    """Ensure the verifier is pinned to the committed, versioned manifest schema."""
    schema_path = root / "V3" / "evidence" / "phase3b_evidence_manifest.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False or "manifest_version" not in required or properties.get("manifest_version", {}).get("const") != "phase3b-gate2-1":
            raise ValueError("schema does not declare the strict Gate 2 contract")
    except (OSError, json.JSONDecodeError, ValueError, AttributeError) as exc:
        _error(errors, "SCHEMA_UNAVAILABLE", "$.manifest_version", f"versioned evidence schema cannot be validated: {exc}", "Restore the committed Gate 2 manifest schema before verifying evidence.")


def _validate_ci_shape(ci: Any, errors: list[VerificationError]) -> None:
    if not isinstance(ci, dict):
        return
    required = {"repository", "run_id", "run_attempt", "workflow_path", "event", "head_sha", "status", "conclusion", "created_at", "started_at", "completed_at", "url", "uploaded_artifact"}
    for key in sorted(required - set(ci)):
        _error(errors, "MISSING_CI_FIELD", f"$.ci.{key}", "required CI identity field is missing", "Regenerate evidence from the Gate 2 workflow.")
    for key in sorted(set(ci) - required):
        _error(errors, "UNKNOWN_CI_FIELD", f"$.ci.{key}", "unknown CI identity field is not permitted", "Use the versioned CI schema.")
    if ci.get("repository") != REPOSITORY:
        _error(errors, "CI_REPOSITORY_MISMATCH", "$.ci.repository", "CI repository does not match the manifest repository", "Use the GitHub Actions repository identity.")
    if not _is_int(ci.get("run_id")) or ci.get("run_id", 0) <= 0:
        _error(errors, "INVALID_RUN_ID", "$.ci.run_id", "run_id must be a positive integer", "Record github.run_id without coercing it to a fabricated string.")
    if not _is_int(ci.get("run_attempt")) or ci.get("run_attempt", 0) <= 0:
        _error(errors, "INVALID_RUN_ATTEMPT", "$.ci.run_attempt", "run_attempt must be a positive integer", "Record github.run_attempt.")
    if not isinstance(ci.get("workflow_path"), str) or not ci.get("workflow_path"):
        _error(errors, "INVALID_WORKFLOW", "$.ci.workflow_path", "workflow_path must be non-empty", "Record the immutable workflow path.")
    if not isinstance(ci.get("event"), str) or not ci.get("event"):
        _error(errors, "INVALID_CI_EVENT", "$.ci.event", "event must be non-empty", "Record the GitHub event name.")
    if not isinstance(ci.get("head_sha"), str) or not SHA_RE.fullmatch(ci.get("head_sha", "")):
        _error(errors, "INVALID_HEAD_SHA", "$.ci.head_sha", "head_sha must be a full lowercase 40-character SHA", "Record the run head SHA.")
    if ci.get("status") != "completed":
        _error(errors, "CI_NOT_COMPLETED", "$.ci.status", "CI status must be completed", "Verify only a completed GitHub run.")
    if ci.get("conclusion") != "success":
        _error(errors, "CI_NOT_SUCCESS", "$.ci.conclusion", "CI conclusion must be success", "Fix the workflow and rerun it.")
    for field in ("created_at", "started_at", "completed_at"):
        if _parse_timestamp(ci.get(field)) is None:
            _error(errors, "INVALID_CI_TIMESTAMP", f"$.ci.{field}", "CI timestamp is not valid ISO-8601", "Copy timestamps from the GitHub API response.")
    if not isinstance(ci.get("url"), str) or not ci.get("url", "").startswith("https://github.com/"):
        _error(errors, "INVALID_RUN_URL", "$.ci.url", "CI URL must be an HTTPS GitHub run URL", "Use the immutable html_url returned by GitHub.")
    artifact = ci.get("uploaded_artifact")
    if not isinstance(artifact, dict):
        _error(errors, "INVALID_UPLOADED_ARTIFACT", "$.ci.uploaded_artifact", "uploaded_artifact must be an object", "Record GitHub artifact identity after upload.")
        return
    for key in ("id", "name", "digest", "url"):
        if key not in artifact:
            _error(errors, "MISSING_UPLOADED_ARTIFACT_FIELD", f"$.ci.uploaded_artifact.{key}", "uploaded artifact field is missing", "Record GitHub's artifact ID, digest, and URL.")
    if not _is_int(artifact.get("id")) or artifact.get("id", 0) <= 0:
        _error(errors, "INVALID_UPLOADED_ARTIFACT_ID", "$.ci.uploaded_artifact.id", "artifact id must be a positive integer", "Use the GitHub-provided artifact ID.")
    if not isinstance(artifact.get("name"), str) or not artifact.get("name"):
        _error(errors, "INVALID_UPLOADED_ARTIFACT_NAME", "$.ci.uploaded_artifact.name", "artifact name must be non-empty", "Use the uploaded artifact name.")
    supplied_digest = artifact.get("digest", "")
    if isinstance(supplied_digest, str) and supplied_digest.startswith("sha256:"):
        supplied_digest = supplied_digest[7:]
    if not isinstance(supplied_digest, str) or not DIGEST_RE.fullmatch(supplied_digest):
        _error(errors, "INVALID_UPLOADED_ARTIFACT_DIGEST", "$.ci.uploaded_artifact.digest", "artifact digest must be a SHA-256 digest", "Use GitHub's artifact digest.")
    if not isinstance(artifact.get("url"), str) or not artifact.get("url", "").startswith("https://github.com/"):
        _error(errors, "INVALID_UPLOADED_ARTIFACT_URL", "$.ci.uploaded_artifact.url", "artifact URL must be an HTTPS GitHub URL", "Use the GitHub artifact URL.")


def _resolve_local_path(root: Path, raw_path: Any, json_path: str, errors: list[VerificationError]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        _error(errors, "INVALID_ARTIFACT_PATH", json_path, "local artifact path must be a non-empty string", "Use a repository-relative file path.")
        return None
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        _error(errors, "UNSAFE_ARTIFACT_PATH", json_path, "artifact path must be relative and cannot traverse parent directories", "Use a repository-relative path without '..'.")
        return None
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(resolved_root)
    except ValueError:
        _error(errors, "ARTIFACT_PATH_ESCAPE", json_path, "artifact path resolves outside the repository root", "Keep evidence files under the repository root.")
        return None
    if not resolved.exists():
        _error(errors, "ARTIFACT_MISSING", json_path, "required artifact does not exist", "Produce and commit/upload the required artifact before verification.")
        return None
    mode = resolved.stat().st_mode
    if not stat.S_ISREG(mode):
        _error(errors, "ARTIFACT_NOT_REGULAR_FILE", json_path, "artifact must be a regular file", "Reference a regular evidence file, not a directory or device.")
        return None
    return resolved


def _validate_artifacts(manifest: dict[str, Any], root: Path, errors: list[VerificationError]) -> dict[str, Path]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        return {}
    if not artifacts:
        _error(errors, "EMPTY_ARTIFACTS", "$.artifacts", "artifact inventory cannot be empty", "Record all required Gate 2 artifact roles.")
        return {}
    seen_roles: set[str] = set()
    seen_paths: set[str] = set()
    paths: dict[str, Path] = {}
    allowed_roles = set(REQUIRED_ARTIFACT_ROLES) | {"tamper_matrix", "gate2_build_report", "mutation_scoreboard", "pip_freeze", "manifest"}
    for index, item in enumerate(artifacts):
        path = f"$.artifacts[{index}]"
        if not isinstance(item, dict):
            _error(errors, "ARTIFACT_ENTRY_TYPE", path, "artifact entry must be an object", "Use the versioned artifact entry shape.")
            continue
        required = {"role", "path", "sha256", "byte_size", "media_type", "producing_command"}
        for key in sorted(required - set(item)):
            _error(errors, "MISSING_ARTIFACT_FIELD", f"{path}.{key}", "artifact field is missing", "Regenerate artifact metadata.")
        for key in sorted(set(item) - required):
            _error(errors, "UNKNOWN_ARTIFACT_FIELD", f"{path}.{key}", "unknown artifact field is not permitted", "Use the versioned artifact entry shape.")
        role = item.get("role")
        if not isinstance(role, str) or not role:
            _error(errors, "INVALID_ARTIFACT_ROLE", f"{path}.role", "artifact role must be a non-empty string", "Use an approved artifact role.")
            continue
        if role not in allowed_roles:
            _error(errors, "UNAPPROVED_ARTIFACT_ROLE", f"{path}.role", "artifact role is not in the approved inventory", "Use a required or documented optional Gate 2 role.")
        if role in seen_roles:
            _error(errors, "DUPLICATE_ARTIFACT_ROLE", f"{path}.role", "artifact role appears more than once", "Provide exactly one artifact for each role.")
        seen_roles.add(role)
        local = _resolve_local_path(root, item.get("path"), f"{path}.path", errors)
        if local is not None:
            relative = local.relative_to(root.resolve()).as_posix()
            if relative in seen_paths:
                _error(errors, "DUPLICATE_ARTIFACT_PATH", f"{path}.path", "artifact path appears more than once", "Use distinct evidence files for each role.")
            seen_paths.add(relative)
            paths[role] = local
        sha = item.get("sha256")
        if not isinstance(sha, str) or not DIGEST_RE.fullmatch(sha):
            _error(errors, "INVALID_ARTIFACT_DIGEST", f"{path}.sha256", "artifact sha256 must be 64 lowercase hexadecimal characters", "Record the SHA-256 digest of the exact bytes.")
        size = item.get("byte_size")
        if not _is_int(size) or size < 0:
            _error(errors, "INVALID_ARTIFACT_SIZE", f"{path}.byte_size", "byte_size must be a non-negative integer", "Record the exact file size in bytes.")
        if not isinstance(item.get("media_type"), str) or not item.get("media_type"):
            _error(errors, "INVALID_ARTIFACT_MEDIA_TYPE", f"{path}.media_type", "media_type must be non-empty", "Record the artifact media type.")
        if not isinstance(item.get("producing_command"), str) or not item.get("producing_command"):
            _error(errors, "INVALID_ARTIFACT_COMMAND", f"{path}.producing_command", "producing_command must be non-empty", "Reference the command or CI step that produced the artifact.")
        if local is not None and isinstance(sha, str) and DIGEST_RE.fullmatch(sha) and digest(local) != sha:
            _error(errors, "ARTIFACT_DIGEST_MISMATCH", f"{path}.sha256", "artifact bytes do not match the claimed digest", "Regenerate the manifest from the exact artifact bytes.")
        if local is not None and _is_int(size) and local.stat().st_size != size:
            _error(errors, "ARTIFACT_SIZE_MISMATCH", f"{path}.byte_size", "artifact size does not match the claimed byte size", "Regenerate the manifest with the exact file size.")
    for role in REQUIRED_ARTIFACT_ROLES:
        if role not in seen_roles:
            _error(errors, "MISSING_REQUIRED_ARTIFACT_ROLE", "$.artifacts", f"required artifact role is missing: {role}", "Produce every required Gate 2 artifact.")
    return paths


def _validate_commands(manifest: dict[str, Any], artifact_paths: dict[str, Path], errors: list[VerificationError]) -> None:
    commands = manifest.get("commands")
    if not isinstance(commands, list):
        return
    seen: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(commands):
        path = f"$.commands[{index}]"
        if not isinstance(item, dict):
            _error(errors, "COMMAND_ENTRY_TYPE", path, "command result must be an object", "Record the structured command result.")
            continue
        required = {"id", "argv", "exit_code", "started_at", "ended_at", "environment", "output", "output_sha256", "artifact_refs", "result_counts"}
        for key in sorted(required - set(item)):
            _error(errors, "MISSING_COMMAND_FIELD", f"{path}.{key}", "required command result field is missing", "Regenerate command evidence with the Gate 2 runner.")
        command_id = item.get("id")
        if not isinstance(command_id, str) or not command_id:
            _error(errors, "INVALID_COMMAND_ID", f"{path}.id", "command id must be non-empty", "Use a stable command ID.")
            continue
        if command_id in seen:
            _error(errors, "DUPLICATE_COMMAND_ID", f"{path}.id", "command id appears more than once", "Provide one result per stable command ID.")
        seen.add(command_id)
        by_id[command_id] = item
        if not isinstance(item.get("argv"), list) or not item.get("argv") or not all(isinstance(value, str) for value in item.get("argv", [])):
            _error(errors, "INVALID_COMMAND_ARGV", f"{path}.argv", "argv must be a non-empty string array", "Record the exact executed argv.")
        if not _is_int(item.get("exit_code")):
            _error(errors, "INVALID_EXIT_CODE", f"{path}.exit_code", "exit_code must be an integer", "Record the subprocess exit code.")
        elif item.get("exit_code") != 0:
            _error(errors, "COMMAND_FAILED", f"{path}.exit_code", "required command exited nonzero", "Fix the failed command and rerun Gate 2.")
        for field in ("started_at", "ended_at"):
            if _parse_timestamp(item.get(field)) is None:
                _error(errors, "INVALID_COMMAND_TIMESTAMP", f"{path}.{field}", "command timestamp is invalid", "Record UTC ISO-8601 command timestamps.")
        if not isinstance(item.get("environment"), dict):
            _error(errors, "INVALID_COMMAND_ENVIRONMENT", f"{path}.environment", "environment must be a summary object", "Record a non-secret environment summary.")
        output = item.get("output")
        output_sha = item.get("output_sha256")
        if not isinstance(output, dict) or not isinstance(output_sha, str) or not DIGEST_RE.fullmatch(output_sha):
            _error(errors, "INVALID_COMMAND_OUTPUT", path, "command output and output_sha256 are required", "Record canonical stdout/stderr output and its digest.")
        elif _canonical_output_digest(output) != output_sha:
            _error(errors, "COMMAND_OUTPUT_DIGEST_MISMATCH", f"{path}.output_sha256", "command output does not match output_sha256", "Regenerate the command result from captured output.")
        refs = item.get("artifact_refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(value, str) for value in refs):
            _error(errors, "INVALID_COMMAND_ARTIFACT_REFS", f"{path}.artifact_refs", "each command must reference a produced artifact role", "Reference the structured result artifact.")
        else:
            for role in refs:
                if role not in artifact_paths and role not in REQUIRED_ARTIFACT_ROLES:
                    _error(errors, "UNKNOWN_COMMAND_ARTIFACT_REF", f"{path}.artifact_refs", f"unknown artifact role: {role}", "Reference an artifact role from the manifest.")
        if not isinstance(item.get("result_counts"), dict):
            _error(errors, "INVALID_RESULT_COUNTS", f"{path}.result_counts", "result_counts must be an object", "Record structured pass/fail counts.")
    for command_id in REQUIRED_COMMAND_IDS:
        if command_id not in seen:
            _error(errors, "MISSING_REQUIRED_COMMAND", "$.commands", f"required command result is missing: {command_id}", "Run the complete Gate 2 command sequence.")
    for command_id, item in by_id.items():
        for role in item.get("artifact_refs", []) if isinstance(item.get("artifact_refs"), list) else []:
            path = artifact_paths.get(role)
            if path is None or path.suffix.lower() != ".json":
                continue
            try:
                structured = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            artifact_counts = structured.get("counts") if isinstance(structured, dict) else None
            if isinstance(artifact_counts, dict) and artifact_counts != item.get("result_counts"):
                _error(errors, "RESULT_COUNT_MISMATCH", f"$.commands[{command_id}].result_counts", "command result counts disagree with its structured artifact", "Regenerate both the command result and structured artifact from one run.")


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)


def _validate_commits(manifest: dict[str, Any], root: Path, errors: list[VerificationError]) -> None:
    values = {field: manifest.get(field) for field in ("source_commit_sha", "reviewed_commit_sha", "evidence_commit_sha")}
    if any(not isinstance(value, str) or not SHA_RE.fullmatch(value) for value in values.values()):
        return
    top = _git(root, ["rev-parse", "--show-toplevel"])
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
        _error(errors, "REPOSITORY_ROOT_INVALID", "$", "repository root is not a Git worktree matching the verification root", "Run verification from the intended repository root.")
        return
    for field, sha in values.items():
        if _git(root, ["cat-file", "-e", f"{sha}^{{commit}}"]).returncode != 0:
            _error(errors, "COMMIT_NOT_FOUND", f"$.{field}", f"{field} does not resolve to a commit in this repository", "Use a real commit SHA from this repository.")
    if values["source_commit_sha"] == values["evidence_commit_sha"]:
        _error(errors, "NON_INDEPENDENT_PROVENANCE", "$.evidence_commit_sha", "source and evidence commits must not be the same claim identity", "Use a later evidence commit or an explicit external evidence identity.")
    for ancestor, descendant in (("source_commit_sha", "reviewed_commit_sha"), ("reviewed_commit_sha", "evidence_commit_sha")):
        if _git(root, ["merge-base", "--is-ancestor", values[ancestor], values[descendant]]).returncode != 0:
            _error(errors, "COMMIT_ANCESTRY_INVALID", f"$.{descendant}", f"{descendant} is not a descendant of {ancestor}", "Use a source/reviewed/evidence chain from the same repository history.")


class GitHubAPI:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    def get_json(self, path: str) -> dict[str, Any]:
        if not self.token:
            try:
                token_result = subprocess.run(["gh", "auth", "token"], text=True, capture_output=True, check=False, timeout=10)
                if token_result.returncode == 0:
                    self.token = token_result.stdout.strip()
            except (OSError, subprocess.SubprocessError):
                pass
        if not self.token:
            raise RuntimeError("GitHub authentication is unavailable")
        request = urllib.request.Request("https://api.github.com" + path, headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {self.token}", "X-GitHub-Api-Version": "2022-11-28"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                value = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"GitHub API verification failed: {type(exc).__name__}") from exc
        if not isinstance(value, dict):
            raise RuntimeError("GitHub API returned a non-object response")
        return value

    def run(self, repository: str, run_id: int) -> dict[str, Any]:
        return self.get_json(f"/repos/{repository}/actions/runs/{run_id}")

    def artifacts(self, repository: str, run_id: int) -> dict[str, Any]:
        return self.get_json(f"/repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100")


def _validate_ci_online(manifest: dict[str, Any], errors: list[VerificationError], github: Any | None) -> None:
    ci = manifest.get("ci")
    if not isinstance(ci, dict) or not _is_int(ci.get("run_id")):
        return
    github = github or GitHubAPI()
    try:
        run = github.run(REPOSITORY, ci["run_id"])
        artifacts_response = github.artifacts(REPOSITORY, ci["run_id"])
    except Exception as exc:
        _error(errors, "CI_VERIFICATION_UNAVAILABLE", "$.ci", str(exc), "Provide GitHub authentication and network access, then rerun online verification.")
        return
    comparisons = (("repository", run.get("repository", {}).get("full_name")), ("head_sha", run.get("head_sha")), ("status", run.get("status")), ("conclusion", run.get("conclusion")), ("workflow_path", run.get("path")), ("event", run.get("event")), ("url", run.get("html_url")), ("created_at", run.get("created_at")), ("started_at", run.get("run_started_at")), ("completed_at", run.get("updated_at")))
    for field, actual in comparisons:
        if ci.get(field) != actual:
            _error(errors, "CI_FIELD_MISMATCH", f"$.ci.{field}", f"manifest CI {field} does not match GitHub", "Copy the immutable value from the verified GitHub run.")
    if run.get("id") != ci.get("run_id"):
        _error(errors, "CI_RUN_ID_MISMATCH", "$.ci.run_id", "manifest run_id does not match the GitHub run response", "Use the GitHub-provided run ID.")
    uploaded = ci.get("uploaded_artifact", {})
    matches = [item for item in artifacts_response.get("artifacts", []) if isinstance(item, dict) and item.get("id") == uploaded.get("id")]
    if not matches:
        _error(errors, "CI_ARTIFACT_MISSING", "$.ci.uploaded_artifact.id", "uploaded artifact is not attached to the verified run", "Use the artifact ID returned by the same GitHub run.")
        return
    artifact = matches[0]
    if artifact.get("workflow_run", {}).get("head_sha") not in {None, ci.get("head_sha")}:
        _error(errors, "CI_ARTIFACT_HEAD_MISMATCH", "$.ci.uploaded_artifact", "uploaded artifact belongs to a different run head SHA", "Use an artifact uploaded by the reviewed commit's run.")
    actual_digest = str(artifact.get("digest", "")).removeprefix("sha256:")
    claimed_digest = str(uploaded.get("digest", "")).removeprefix("sha256:")
    if actual_digest != claimed_digest:
        _error(errors, "CI_ARTIFACT_DIGEST_MISMATCH", "$.ci.uploaded_artifact.digest", "manifest digest does not match GitHub's artifact digest", "Copy GitHub's artifact digest exactly.")


def verify_manifest(manifest_path: Path, *, repo_root: Path | None = None, offline: bool = False, github: Any | None = None) -> dict[str, Any]:
    root = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    errors: list[VerificationError] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _error(errors, "MANIFEST_MISSING", "$", "manifest file does not exist", "Generate the Gate 2 evidence manifest.")
        return {"status": "EVIDENCE_INVALID", "errors": [item.to_dict() for item in errors]}
    except json.JSONDecodeError as exc:
        _error(errors, "INVALID_JSON", "$", f"manifest is not valid JSON: {exc.msg}", "Regenerate a valid JSON manifest.")
        return {"status": "EVIDENCE_INVALID", "errors": [item.to_dict() for item in errors]}
    _validate_schema_contract(root, errors)
    _validate_shape(manifest, errors)
    if isinstance(manifest, dict):
        _validate_ci_shape(manifest.get("ci"), errors)
        artifacts = _validate_artifacts(manifest, root, errors)
        _validate_commands(manifest, artifacts, errors)
        _validate_commits(manifest, root, errors)
        if isinstance(manifest.get("ci"), dict) and isinstance(manifest["ci"].get("head_sha"), str) and manifest["ci"].get("head_sha") != manifest.get("reviewed_commit_sha"):
            _error(errors, "CI_HEAD_REVIEWED_MISMATCH", "$.ci.head_sha", "verified CI head_sha must equal reviewed_commit_sha", "Bind the evidence to the exact independently reviewed commit.")
        if not offline and not errors:
            _validate_ci_online(manifest, errors, github)
    if errors:
        return {"status": "EVIDENCE_INVALID", "errors": [item.to_dict() for item in errors]}
    if offline:
        return {"status": "OFFLINE_PARTIAL_VERIFICATION", "errors": [], "message": "Local schema, artifact bytes, command integrity, and Git ancestry passed; GitHub CI was not verified online."}
    return {"status": "EVIDENCE_VALID", "errors": []}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--offline", action="store_true", help="verify local structure only and return OFFLINE_PARTIAL_VERIFICATION")
    args = parser.parse_args()
    result = verify_manifest(args.manifest, repo_root=args.repo_root, offline=args.offline)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] == "EVIDENCE_VALID":
        return 0
    if result["status"] == "OFFLINE_PARTIAL_VERIFICATION":
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
