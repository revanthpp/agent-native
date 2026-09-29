"""Produce a machine-readable builder evidence manifest for the RC1 handoff."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _run(root: Path, command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)
    return {"command": command, "returncode": completed.returncode, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("V3/evidence/phase3_rc1_builder_manifest.json"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    started = datetime.now(timezone.utc)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=False).stdout.strip()
    commands = [
        [sys.executable, "-m", "pytest", "-q", "tests/packs", "--import-mode=importlib"],
        [sys.executable, "-m", "pytest", "-q", "--import-mode=importlib", "--ignore=audit_v2"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        [sys.executable, "scripts/run_phase2b_mutations.py"],
        [sys.executable, "scripts/run_phase2c_mutations.py"],
        [sys.executable, "scripts/run_phase3_mutations.py"],
    ]
    results = [_run(root, command) for command in commands]
    completed = datetime.now(timezone.utc)
    manifest = {
        "run_id": "phase3-rc1-builder-" + started.strftime("%Y%m%dT%H%M%SZ"),
        "repository": "github.com/revanthpp/agent-native",
        "commit_sha": commit,
        "package_version": "2.0.0a1",
        "python_version": sys.version,
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "completed_at": completed.isoformat().replace("+00:00", "Z"),
        "commands": results,
        "results": {"tests": results[0:3], "mutations": results[3:]},
        "artifacts": ["V3/PHASE_3_RC1_BUILD_REPORT.md", "V3/REQUIREMENTS_TRACEABILITY.md"],
        "status": "BUILDER_EVIDENCE_ONLY" if all(item["returncode"] == 0 for item in results) else "BUILDER_VERIFICATION_FAILED",
    }
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "output": str(output), "commit_sha": commit}, indent=2))
    return 0 if manifest["status"] == "BUILDER_EVIDENCE_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
