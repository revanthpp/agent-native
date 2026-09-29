"""Run the first-party 30-case Gate 2 evidence tamper matrix."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_phase3b_evidence import _canonical_output_digest, digest, verify_manifest


class FakeGitHub:
    def __init__(self, manifest: dict, *, run: dict | None = None, artifacts: dict | None = None, failure: str | None = None):
        self.manifest = manifest
        self._run = run
        self._artifacts = artifacts
        self.failure = failure

    def run(self, repository: str, run_id: int) -> dict:
        if self.failure:
            raise RuntimeError(self.failure)
        ci = self.manifest["ci"]
        return self._run or {"id": run_id, "repository": {"full_name": repository}, "head_sha": ci["head_sha"], "status": ci["status"], "conclusion": ci["conclusion"], "path": ci["workflow_path"], "event": ci["event"], "html_url": ci["url"], "created_at": ci["created_at"], "run_started_at": ci["started_at"], "updated_at": ci["completed_at"]}

    def artifacts(self, repository: str, run_id: int) -> dict:
        if self.failure:
            raise RuntimeError(self.failure)
        ci = self.manifest["ci"]
        return self._artifacts or {"artifacts": [{"id": ci["uploaded_artifact"]["id"], "digest": "sha256:" + ci["uploaded_artifact"]["digest"], "workflow_run": {}}]}


def _base_manifest() -> dict:
    commits = subprocess.run(["git", "rev-list", "--max-count=5", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.splitlines()
    if len(commits) < 4:
        raise RuntimeError("Gate 2 tamper matrix requires at least four local commits")
    source, reviewed, evidence = commits[3], commits[1], commits[0]
    paths = [
        "V3/PHASE_3B_PRODUCTIZATION_BUILD_REPORT.md", "V3/REQUIREMENTS_TRACEABILITY.md", "pyproject.toml",
        "audit_v3/phase3b_closure/rerun_01/findings.json", "audit_v3/phase3b_closure/rerun_01/environment.json",
        "audit_v3/phase3b_closure/rerun_01/commands.log", "audit_v3/phase3b_closure/rerun_01/INDEPENDENT_REVIEW_RESULT.md", "README.md",
    ]
    wheel = sorted((ROOT / "dist").glob("agentnative-*.whl"))
    if wheel:
        paths[2] = wheel[-1].relative_to(ROOT).as_posix()
    structured_path = ROOT / "V3" / "evidence" / "gate2" / "structured_test_result.json"
    if not structured_path.exists():
        structured_path = ROOT / "V3" / "evidence" / "phase3b_tamper_structured_fixture.json"
    paths[3] = structured_path.relative_to(ROOT).as_posix()
    roles = ("closure_build_report", "requirements_traceability", "wheel", "structured_test_result", "phase2b_mutation_result", "phase2c_mutation_result", "phase3_mutation_result", "wheel_smoke_result")
    artifacts = []
    for role, relative in zip(roles, paths):
        path = ROOT / relative
        artifacts.append({"role": role, "path": relative, "sha256": digest(path), "byte_size": path.stat().st_size, "media_type": "application/octet-stream" if path.suffix == ".whl" else "text/plain", "producing_command": "gate2-tamper-fixture"})
    optional_paths = {"tamper_matrix": "V3/evidence/gate2/evidence_tamper_matrix.json" if (ROOT / "V3/evidence/gate2/evidence_tamper_matrix.json").exists() else "V3/evidence/phase3b_tamper_structured_fixture.json", "gate2_build_report": "V3/PHASE_3B_GATE2_PROOF_REMEDIATION_BUILD_REPORT.md"}
    for role, relative in optional_paths.items():
        path = ROOT / relative
        artifacts.append({"role": role, "path": relative, "sha256": digest(path), "byte_size": path.stat().st_size, "media_type": "application/json" if path.suffix == ".json" else "text/markdown", "producing_command": "gate2-tamper-fixture"})
    commands = []
    command_roles = {"baseline_tests": "structured_test_result", "evidence_tamper_matrix": "tamper_matrix", "phase3_mutations": "phase3_mutation_result", "wheel_smoke": "wheel_smoke_result", "manifest_generation": "gate2_build_report", "manifest_local_verification": "gate2_build_report"}
    role_paths = {role: relative for role, relative in zip(roles, paths)} | optional_paths
    for command_id in ("baseline_tests", "evidence_tamper_matrix", "phase3_mutations", "wheel_smoke", "manifest_generation", "manifest_local_verification"):
        role = command_roles[command_id]
        output = {"stdout": "", "stderr": ""}
        result_counts = {}
        candidate = ROOT / role_paths.get(role, "")
        try:
            result_counts = json.loads(candidate.read_text(encoding="utf-8")).get("counts", {})
        except (OSError, json.JSONDecodeError):
            pass
        commands.append({"id": command_id, "argv": ["gate2-tamper-fixture", command_id], "exit_code": 0, "started_at": "2026-09-28T12:00:00Z", "ended_at": "2026-09-28T12:00:01Z", "environment": {"python": "fixture"}, "output": output, "output_sha256": _canonical_output_digest(output), "artifact_refs": [role], "result_counts": result_counts})
    return {"manifest_version": "phase3b-gate2-1", "status": "BUILDER_EVIDENCE_ONLY", "repository": "revanthpp/agent-native", "source_commit_sha": source, "reviewed_commit_sha": reviewed, "evidence_commit_sha": evidence, "generated_at": "2026-09-28T12:00:00Z", "generator_version": "tamper-fixture", "ci": {"repository": "revanthpp/agent-native", "run_id": 123, "run_attempt": 1, "workflow_path": ".github/workflows/ci.yml", "event": "push", "head_sha": reviewed, "status": "completed", "conclusion": "success", "created_at": "2026-09-28T11:59:00Z", "started_at": "2026-09-28T12:00:00Z", "completed_at": "2026-09-28T12:01:00Z", "url": "https://github.com/revanthpp/agent-native/actions/runs/123", "uploaded_artifact": {"id": 456, "name": "gate2", "digest": "a" * 64, "url": "https://github.com/revanthpp/agent-native/actions/artifacts/456"}}, "artifacts": artifacts, "commands": commands, "results": {"counts": {"passed": 1}}}


def _write_manifest(manifest: dict) -> Path:
    handle = tempfile.NamedTemporaryFile(prefix="gate2-tamper-", suffix=".json", dir=ROOT, delete=False, mode="w", encoding="utf-8")
    json.dump(manifest, handle, indent=2)
    handle.close()
    return Path(handle.name)


def _offline_cli(path: Path) -> tuple[int, dict]:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts/verify_phase3b_evidence.py"), str(path), "--offline", "--repo-root", str(ROOT)], cwd=ROOT, text=True, capture_output=True, check=False)
    return completed.returncode, json.loads(completed.stdout)


def main() -> int:
    base = _base_manifest()
    cases: list[tuple[str, dict, FakeGitHub | None, bool]] = []
    def add(name: str, mutate, *, online=False, fake=None):
        value = copy.deepcopy(base)
        mutate(value)
        cases.append((name, value, fake, online))

    add("missing_manifest", lambda value: value, online=False)
    add("invalid_json", lambda value: value, online=False)
    add("missing_artifacts", lambda value: value.pop("artifacts"), online=False)
    add("empty_artifacts", lambda value: value.__setitem__("artifacts", []), online=False)
    add("missing_required_artifact_role", lambda value: value.__setitem__("artifacts", [item for item in value["artifacts"] if item["role"] != "wheel"]), online=False)
    add("nonexistent_artifact_path", lambda value: value["artifacts"][0].__setitem__("path", "V3/evidence/no-such-file.json"), online=False)
    add("path_traversal", lambda value: value["artifacts"][0].__setitem__("path", "../outside.txt"), online=False)
    symlink = ROOT / "V3" / "evidence" / ".gate2-tamper-escape"
    escape_target = Path(tempfile.mkstemp(prefix="gate2-escape-")[1])
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(escape_target)
    add("symlink_escape", lambda value: value["artifacts"][0].__setitem__("path", symlink.relative_to(ROOT).as_posix()), online=False)
    add("altered_artifact_bytes", lambda value: value["artifacts"][0].__setitem__("sha256", "b" * 64), online=False)
    add("absent_digest", lambda value: value["artifacts"][0].pop("sha256"), online=False)
    add("malformed_digest", lambda value: value["artifacts"][0].__setitem__("sha256", "not-a-digest"), online=False)
    add("incorrect_byte_size", lambda value: value["artifacts"][0].__setitem__("byte_size", 1), online=False)
    add("arbitrary_source_sha", lambda value: value.__setitem__("source_commit_sha", "1" * 40), online=False)
    add("arbitrary_evidence_sha", lambda value: value.__setitem__("evidence_commit_sha", "2" * 40), online=False)
    add("arbitrary_reviewed_sha", lambda value: value.__setitem__("reviewed_commit_sha", "3" * 40), online=False)
    add("equal_source_evidence_sha", lambda value: value.__setitem__("evidence_commit_sha", value["source_commit_sha"]), online=False)
    add("valid_unrelated_repository_commit", lambda value: value.__setitem__("source_commit_sha", "f" * 40), online=False)
    add("nonexistent_ci_run", lambda value: value, online=True, fake=FakeGitHub(base, failure="GitHub run not found"))
    add("ci_from_another_repository", lambda value: value, online=True, fake=FakeGitHub(base, run={"id": 123, "repository": {"full_name": "other/repository"}, "head_sha": base["ci"]["head_sha"], "status": "completed", "conclusion": "success", "path": base["ci"]["workflow_path"], "event": "push", "html_url": base["ci"]["url"], "created_at": base["ci"]["created_at"], "run_started_at": base["ci"]["started_at"], "updated_at": base["ci"]["completed_at"]}))
    add("ci_for_another_head_sha", lambda value: value, online=True, fake=FakeGitHub(base, run={"id": 123, "repository": {"full_name": "revanthpp/agent-native"}, "head_sha": "f" * 40, "status": "completed", "conclusion": "success", "path": base["ci"]["workflow_path"], "event": "push", "html_url": base["ci"]["url"], "created_at": base["ci"]["created_at"], "run_started_at": base["ci"]["started_at"], "updated_at": base["ci"]["completed_at"]}))
    add("ci_in_progress", lambda value: value["ci"].__setitem__("status", "in_progress"), online=False)
    add("ci_failed", lambda value: value["ci"].__setitem__("conclusion", "failure"), online=False)
    add("fabricated_run_url", lambda value: value["ci"].__setitem__("url", "https://github.com/revanthpp/agent-native/actions/runs/999999999"), online=True, fake=FakeGitHub(base))
    add("mismatched_workflow", lambda value: value["ci"].__setitem__("workflow_path", ".github/workflows/other.yml"), online=True, fake=FakeGitHub(base))
    add("missing_uploaded_artifact", lambda value: value, online=True, fake=FakeGitHub(base, artifacts={"artifacts": []}))
    add("mismatched_github_artifact_digest", lambda value: value, online=True, fake=FakeGitHub(base, artifacts={"artifacts": [{"id": 456, "digest": "sha256:" + "b" * 64, "workflow_run": {}}]}))
    add("missing_required_command", lambda value: value.__setitem__("commands", [item for item in value["commands"] if item["id"] != "wheel_smoke"]), online=False)
    add("nonzero_required_command", lambda value: value["commands"][0].__setitem__("exit_code", 1), online=False)
    add("inconsistent_test_count", lambda value: value["commands"][0].__setitem__("result_counts", {"passed": 999}), online=False)
    add("status_changed", lambda value: value.__setitem__("status", "PHASE_3B_INDEPENDENTLY_VERIFIED"), online=False)

    results = []
    try:
        for name, manifest, fake, online in cases:
            if name == "missing_manifest":
                missing = ROOT / "V3" / "evidence" / ".gate2-missing-manifest.json"
                missing.unlink(missing_ok=True)
                code, output = _offline_cli(missing)
            elif name == "invalid_json":
                path = ROOT / "V3" / "evidence" / ".gate2-invalid-manifest.json"
                path.write_text("{not-json", encoding="utf-8")
                code, output = _offline_cli(path)
                path.unlink(missing_ok=True)
            else:
                path = _write_manifest(manifest)
                try:
                    if online:
                        output = verify_manifest(path, repo_root=ROOT, offline=False, github=fake)
                        code = 0 if output["status"] == "EVIDENCE_VALID" else 1
                    else:
                        code, output = _offline_cli(path)
                finally:
                    path.unlink(missing_ok=True)
            results.append({"case": name, "returncode": code, "status": output.get("status"), "accepted": code == 0 or output.get("status") == "EVIDENCE_VALID", "error_codes": sorted({item.get("error_code") for item in output.get("errors", [])})})
    finally:
        symlink.unlink(missing_ok=True)
        escape_target.unlink(missing_ok=True)
    passed = sum(1 for item in results if not item["accepted"])
    online_path = _write_manifest(base)
    offline_path = _write_manifest(base)
    try:
        known_good_online = verify_manifest(online_path, repo_root=ROOT, offline=False, github=FakeGitHub(base))["status"]
        known_good_offline = verify_manifest(offline_path, repo_root=ROOT, offline=True)["status"]
    finally:
        online_path.unlink(missing_ok=True)
        offline_path.unlink(missing_ok=True)
    payload = {"schema_version": "phase3b-evidence-tamper-matrix-1", "status": "PASS" if len(results) == 30 and passed == 30 else "FAIL", "counts": {"total": len(results), "rejected": passed, "accepted": len(results) - passed}, "cases": results, "known_good_online": known_good_online, "known_good_offline": known_good_offline}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
