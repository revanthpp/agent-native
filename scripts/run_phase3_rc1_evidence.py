"""Produce a machine-readable builder evidence manifest for the RC1 handoff."""

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


def _run(root: Path, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}


def _digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("V3/evidence/phase3_rc1_builder_manifest.json"))
    parser.add_argument("--evidence-commit-sha", default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    started = datetime.now(timezone.utc)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False).stdout.strip()
    wheels = sorted((root / "dist").glob("agentnative-*.whl"))
    commands = [
        [sys.executable, "-m", "pytest", "-q", "tests/packs", "--import-mode=importlib"],
        [sys.executable, "-m", "pytest", "-q", "--import-mode=importlib", "--ignore=audit_v2"],
        [sys.executable, "-m", "pytest", "-q", "tests/retail/test_closure_remediation.py", "--import-mode=importlib"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        [sys.executable, "scripts/run_phase2b_mutations.py"],
        [sys.executable, "scripts/run_phase2c_mutations.py"],
        [sys.executable, "scripts/run_phase3_mutations.py"],
    ]
    if wheels and os.environ.get("SKIP_LOCAL_WHEEL_SMOKE") != "1":
        commands.append([sys.executable, "scripts/run_phase3b_wheel_smoke.py", str(wheels[-1])])
    results = [_run(root, command) for command in commands]
    completed = datetime.now(timezone.utc)
    artifact_paths = [root / "V3/PHASE_3_RC1_BUILD_REPORT.md", root / "V3/PHASE_3B_PRODUCTIZATION_BUILD_REPORT.md", root / "V3/REQUIREMENTS_TRACEABILITY.md"]
    manifest = {
        "run_id": "phase3-rc1-builder-" + started.strftime("%Y%m%dT%H%M%SZ"),
        "repository": "github.com/revanthpp/agent-native",
        "source_commit_sha": commit,
        "evidence_commit_sha": args.evidence_commit_sha or os.environ.get("EVIDENCE_COMMIT_SHA"),
        "package_version": "2.0.0a1",
        "python_version": sys.version,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": completed.isoformat().replace("+00:00", "Z"),
        "commands": results,
        "results": {"tests": results[0:4], "mutations": results[4:]},
        "ci": {"repository": os.environ.get("GITHUB_REPOSITORY", "local"), "workflow": os.environ.get("GITHUB_WORKFLOW", "local-builder"), "run_id": os.environ.get("GITHUB_RUN_ID"), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"), "event": os.environ.get("GITHUB_EVENT_NAME"), "runner_image": os.environ.get("RUNNER_OS", "local")},
        "artifacts": [{"path": str(path.relative_to(root)), "sha256": _digest(path)} for path in artifact_paths],
        "status": "BUILDER_EVIDENCE_ONLY" if all(item["returncode"] == 0 for item in results) else "BUILDER_VERIFICATION_FAILED",
    }
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=str(output.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(json.dumps({"status": manifest["status"], "output": str(output), "source_commit_sha": commit}, indent=2))
    return 0 if manifest["status"] == "BUILDER_EVIDENCE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
