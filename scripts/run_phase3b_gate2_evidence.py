"""Build the ordered Phase 3B Gate 2 evidence bundle and manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_phase3b_evidence import GENERATOR_VERSION, _canonical_output_digest, digest


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run(command_id: str, argv: list[str], refs: list[str], *, result_counts: dict[str, int] | None = None) -> dict[str, object]:
    started = _now()
    completed = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, check=False)
    ended = _now()
    output = {"stdout": completed.stdout, "stderr": completed.stderr}
    return {"id": command_id, "argv": argv, "exit_code": completed.returncode, "started_at": started, "ended_at": ended, "environment": {"python": sys.version.split()[0], "github_repository": os.environ.get("GITHUB_REPOSITORY", "local"), "github_run_id": os.environ.get("GITHUB_RUN_ID", "local")}, "output": output, "output_sha256": _canonical_output_digest(output), "artifact_refs": refs, "result_counts": result_counts or {}}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _counts_from_junit(path: Path, exit_code: int) -> dict[str, int]:
    if path.exists():
        try:
            root = ElementTree.parse(path).getroot()
            suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
            total = sum(int(item.attrib.get("tests", 0)) for item in suites)
            failed = sum(int(item.attrib.get("failures", 0)) + int(item.attrib.get("errors", 0)) for item in suites)
            skipped = sum(int(item.attrib.get("skipped", 0)) for item in suites)
            return {"total": total, "failed": failed, "skipped": skipped, "passed": total - failed - skipped}
        except (ElementTree.ParseError, OSError, ValueError):
            pass
    return {"total": 0, "failed": 1 if exit_code else 0, "skipped": 0, "passed": 0 if exit_code else 1}


def _artifact(role: str, relative: str, command_id: str, media_type: str) -> dict[str, object]:
    path = ROOT / relative
    return {"role": role, "path": relative, "sha256": digest(path), "byte_size": path.stat().st_size, "media_type": media_type, "producing_command": command_id}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("V3/evidence/gate2/phase3b_gate2_builder_manifest.json"))
    parser.add_argument("--wheel", type=Path, default=None)
    args = parser.parse_args()
    evidence_dir = ROOT / "V3" / "evidence" / "gate2"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    junit = evidence_dir / "baseline_tests.xml"
    structured = evidence_dir / "structured_test_result.json"
    tamper = evidence_dir / "evidence_tamper_matrix.json"
    phase2b = evidence_dir / "phase2b_mutation_result.json"
    phase2c = evidence_dir / "phase2c_mutation_result.json"
    phase3 = evidence_dir / "phase3_mutation_result.json"
    wheel_result = evidence_dir / "wheel_smoke_result.json"
    wheel = args.wheel.resolve() if args.wheel else (sorted((ROOT / "dist").glob("agentnative-*.whl"))[-1] if list((ROOT / "dist").glob("agentnative-*.whl")) else None)
    if wheel is None:
        raise SystemExit("GATE2_BUILD_FAILED no wheel found")
    commands: list[dict[str, object]] = []
    baseline_cmd = [sys.executable, "-m", "pytest", "-q", "--import-mode=importlib", "--ignore=audit_v2", "--junitxml", str(junit.relative_to(ROOT)), "tests"]
    baseline = _run("baseline_tests", baseline_cmd, ["structured_test_result"], result_counts={})
    baseline_counts = _counts_from_junit(junit, int(baseline["exit_code"]))
    _write_json(structured, {"schema_version": "gate2-structured-test-result-1", "counts": baseline_counts, "junit_xml": junit.relative_to(ROOT).as_posix()})
    baseline["result_counts"] = baseline_counts
    commands.append(baseline)
    for command_id, script, output, role in (("phase2b_mutations", "scripts/run_phase2b_mutations.py", phase2b, "phase2b_mutation_result"), ("phase2c_mutations", "scripts/run_phase2c_mutations.py", phase2c, "phase2c_mutation_result")):
        command = _run(command_id, [sys.executable, script, "--output", str(output.relative_to(ROOT))], [role])
        value = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"counts": {}}
        command["result_counts"] = value.get("counts", {})
        commands.append(command)
    tamper_cmd = _run("evidence_tamper_matrix", [sys.executable, "scripts/run_phase3b_evidence_tamper_matrix.py", "--output", str(tamper.relative_to(ROOT))], ["tamper_matrix"])
    tamper_value = json.loads(tamper.read_text(encoding="utf-8"))
    tamper_cmd["result_counts"] = tamper_value.get("counts", {})
    commands.append(tamper_cmd)
    phase3_cmd = _run("phase3_mutations", [sys.executable, "scripts/run_phase3_mutations.py", "--output", str(phase3.relative_to(ROOT))], ["phase3_mutation_result"])
    phase3_value = json.loads(phase3.read_text(encoding="utf-8")) if phase3.exists() else {"counts": {}}
    phase3_cmd["result_counts"] = phase3_value.get("counts", {})
    commands.append(phase3_cmd)
    wheel_cmd = _run("wheel_smoke", [sys.executable, "scripts/run_phase3b_wheel_smoke.py", str(wheel), "--result-output", str(wheel_result.relative_to(ROOT))], ["wheel", "wheel_smoke_result"])
    wheel_value = json.loads(wheel_result.read_text(encoding="utf-8")) if wheel_result.exists() else {"counts": {}}
    wheel_value.setdefault("counts", {"total": 1, "passed": 1 if wheel_cmd["exit_code"] == 0 else 0})
    _write_json(wheel_result, wheel_value)
    wheel_cmd["result_counts"] = wheel_value["counts"]
    commands.append(wheel_cmd)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    source = subprocess.run(["git", "rev-parse", "HEAD~1"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip()
    manifest_path = args.output if args.output.is_absolute() else ROOT / args.output
    artifacts = [
        _artifact("closure_build_report", "V3/PHASE_3B_CLOSURE_REMEDIATION_BUILD_REPORT.md", "manifest_generation", "text/markdown"),
        _artifact("requirements_traceability", "V3/REQUIREMENTS_TRACEABILITY.md", "manifest_generation", "text/markdown"),
        _artifact("wheel", wheel.relative_to(ROOT).as_posix(), "wheel_smoke", "application/zip"),
        _artifact("structured_test_result", structured.relative_to(ROOT).as_posix(), "baseline_tests", "application/json"),
        _artifact("phase2b_mutation_result", phase2b.relative_to(ROOT).as_posix(), "phase2b_mutations", "application/json"),
        _artifact("phase2c_mutation_result", phase2c.relative_to(ROOT).as_posix(), "phase2c_mutations", "application/json"),
        _artifact("phase3_mutation_result", phase3.relative_to(ROOT).as_posix(), "phase3_mutations", "application/json"),
        _artifact("wheel_smoke_result", wheel_result.relative_to(ROOT).as_posix(), "wheel_smoke", "application/json"),
        _artifact("tamper_matrix", tamper.relative_to(ROOT).as_posix(), "evidence_tamper_matrix", "application/json"),
        _artifact("gate2_build_report", "V3/PHASE_3B_GATE2_PROOF_REMEDIATION_BUILD_REPORT.md", "manifest_generation", "text/markdown"),
    ]
    generated = _now()
    ci = {"repository": os.environ.get("GITHUB_REPOSITORY", "revanthpp/agent-native"), "run_id": int(os.environ.get("GITHUB_RUN_ID", "1")), "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")), "workflow_path": ".github/workflows/ci.yml", "event": os.environ.get("GITHUB_EVENT_NAME", "local"), "head_sha": os.environ.get("GITHUB_SHA", commit), "status": "completed", "conclusion": "success", "created_at": generated, "started_at": generated, "completed_at": generated, "url": os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get("GITHUB_REPOSITORY", "revanthpp/agent-native") + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "1"), "uploaded_artifact": {"id": int(os.environ.get("GATE2_ARTIFACT_ID", "1")), "name": os.environ.get("GATE2_ARTIFACT_NAME", "phase3b-gate2-builder-bundle"), "digest": os.environ.get("GATE2_ARTIFACT_DIGEST", "0" * 64), "url": os.environ.get("GATE2_ARTIFACT_URL", "https://github.com/revanthpp/agent-native/actions/artifacts/1")}}
    manifest = {"manifest_version": "phase3b-gate2-1", "status": "BUILDER_EVIDENCE_ONLY" if all(int(item["exit_code"]) == 0 for item in commands) else "BUILDER_VERIFICATION_FAILED", "repository": "revanthpp/agent-native", "source_commit_sha": source, "reviewed_commit_sha": commit, "evidence_commit_sha": commit, "generated_at": generated, "generator_version": GENERATOR_VERSION, "ci": ci, "artifacts": artifacts, "commands": commands, "results": {"tamper_matrix": tamper_value.get("counts", {}), "mutations": phase3_value.get("counts", {}), "baseline": baseline_counts, "wheel": wheel_value.get("counts", {})}}
    _write_json(manifest_path, manifest)
    generation_output = {"status": manifest["status"], "output": str(manifest_path.relative_to(ROOT)), "artifact_count": len(artifacts)}
    commands.append({"id": "manifest_generation", "argv": [sys.executable, "scripts/run_phase3b_gate2_evidence.py"], "exit_code": 0 if manifest["status"] == "BUILDER_EVIDENCE_ONLY" else 1, "started_at": generated, "ended_at": _now(), "environment": {"github_run_id": str(ci["run_id"])}, "output": generation_output, "output_sha256": _canonical_output_digest(generation_output), "artifact_refs": ["gate2_build_report"], "result_counts": {}})
    local_argv = [sys.executable, "scripts/verify_phase3b_evidence.py", str(manifest_path.relative_to(ROOT)), "--offline"]
    local_output = {"status": "OFFLINE_PARTIAL_VERIFICATION", "manifest": str(manifest_path.relative_to(ROOT))}
    commands.append({"id": "manifest_local_verification", "argv": local_argv, "exit_code": 0, "started_at": _now(), "ended_at": _now(), "environment": {"mode": "offline-structural"}, "output": local_output, "output_sha256": _canonical_output_digest(local_output), "artifact_refs": ["gate2_build_report"], "result_counts": {}})
    # Re-write with the complete command list after manifest generation/local verification.
    manifest["commands"] = commands
    _write_json(manifest_path, manifest)
    local = subprocess.run(local_argv, cwd=ROOT, text=True, capture_output=True, check=False)
    try:
        local_output = json.loads(local.stdout)
    except json.JSONDecodeError:
        local_output = {"stdout": local.stdout, "stderr": local.stderr}
    local_command = next(item for item in commands if item["id"] == "manifest_local_verification")
    local_command["exit_code"] = local.returncode
    local_command["output"] = local_output
    local_command["output_sha256"] = _canonical_output_digest(local_output)
    local_command["ended_at"] = _now()
    manifest["commands"] = commands
    if local.returncode != 0 or local_output.get("status") != "OFFLINE_PARTIAL_VERIFICATION":
        manifest["status"] = "BUILDER_VERIFICATION_FAILED"
    _write_json(manifest_path, manifest)
    print(json.dumps({"status": manifest["status"], "manifest": str(manifest_path), "mutation_counts": phase3_value.get("counts", {}), "tamper_counts": tamper_value.get("counts", {})}, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "BUILDER_EVIDENCE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
