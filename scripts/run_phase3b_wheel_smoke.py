"""Run the Retail product demo from a hermetic wheel-only environment."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def run_checked(command: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, object]:
    completed = _run(command, cwd=cwd, env=env)
    result = {"argv": command, "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
    if completed.returncode:
        raise SystemExit(f"WHEEL_SMOKE_FAILED exit={completed.returncode}\nstdout={completed.stdout[-2000:]}\nstderr={completed.stderr[-2000:]}")
    return result


def clean_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        environment.pop(key, None)
    return environment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--result-output", type=Path, default=None)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    wheel = args.wheel.resolve()
    if not wheel.exists() or wheel.suffix != ".whl":
        raise SystemExit("WHEEL_SMOKE_FAILED wheel does not exist")
    result: dict[str, object] = {"status": "WHEEL_SMOKE_FAILED", "wheel": str(wheel), "commands": []}
    with tempfile.TemporaryDirectory(prefix="agentnative-wheel-smoke-") as temporary:
        outside = Path(temporary)
        venv = outside / "venv"
        # No system-site-packages: only the wheel and declared dependencies may import.
        result["commands"].append(run_checked([sys.executable, "-m", "venv", str(venv)], cwd=outside, env=clean_environment()))
        executable = venv / "bin" / "python"
        result["commands"].append(run_checked([str(executable), "-m", "pip", "install", str(wheel)], cwd=outside, env=clean_environment()))
        result["commands"].append(run_checked([str(executable), "-m", "pip", "check"], cwd=outside, env=clean_environment()))
        result["commands"].append(run_checked([str(executable), "-m", "pip", "freeze"], cwd=outside, env=clean_environment()))
        inputs = outside / "inputs"
        shutil.copytree(root / "examples" / "retail", inputs)
        environment = clean_environment()
        probe = run_checked([str(executable), "-c", "import agentnative; print(agentnative.__file__)"], cwd=outside, env=environment)
        imported_from = Path(str(probe["stdout"]).strip()).resolve()
        result["import_path"] = str(imported_from)
        if venv.resolve() not in imported_from.parents:
            raise SystemExit(f"WHEEL_SMOKE_FAILED import escaped virtualenv: {imported_from}")
        if root.resolve() in imported_from.parents:
            raise SystemExit(f"WHEEL_SMOKE_FAILED imported source checkout: {imported_from}")
        projects = ("direct-ready", "platform-retailer", "human-handoff-retailer", "unsafe-retailer")
        for project in projects:
            source = inputs / project
            result["commands"].extend([
                run_checked([str(venv / "bin" / "agentnative"), "retail", "validate", str(source)], cwd=outside, env=environment),
                run_checked([str(venv / "bin" / "agentnative"), "retail", "recommend", str(source)], cwd=outside, env=environment),
                run_checked([str(venv / "bin" / "agentnative"), "retail", "simulate", str(source), "--scenario", "lost_response"], cwd=outside, env=environment),
            ])
        negative = _run([str(venv / "bin" / "agentnative"), "retail", "simulate", str(inputs / "direct-ready"), "--scenario", "not-supported"], cwd=outside, env=environment)
        result["commands"].append({"argv": negative.args, "exit_code": negative.returncode, "stdout": negative.stdout, "stderr": negative.stderr})
        if negative.returncode == 0 or "UNKNOWN_SCENARIO" not in negative.stderr:
            raise SystemExit("WHEEL_SMOKE_FAILED negative scenario did not fail closed")
    result["status"] = "WHEEL_SMOKE_PASS"
    result["counts"] = {"total": 5, "passed": 5}
    if args.result_output:
        output = args.result_output if args.result_output.is_absolute() else root / args.result_output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("WHEEL_SMOKE_PASS hermetic wheel-only Retail workflow outside repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
