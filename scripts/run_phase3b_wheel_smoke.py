"""Run the Retail product demo using only the built wheel from outside the repo."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise SystemExit(f"WHEEL_SMOKE_FAILED exit={completed.returncode}\nstdout={completed.stdout[-2000:]}\nstderr={completed.stderr[-2000:]}")


def clean_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    return environment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    wheel = args.wheel.resolve()
    if not wheel.exists() or wheel.suffix != ".whl":
        raise SystemExit("WHEEL_SMOKE_FAILED wheel does not exist")
    with tempfile.TemporaryDirectory(prefix="agentnative-wheel-smoke-") as temporary:
        outside = Path(temporary)
        venv = outside / "venv"
        run([sys.executable, "-m", "venv", "--system-site-packages", str(venv)], cwd=outside, env=clean_environment())
        executable = venv / "bin" / "agentnative"
        run([str(venv / "bin" / "python"), "-m", "pip", "install", str(wheel)], cwd=outside, env=clean_environment())
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        projects = ("direct-ready", "platform-retailer", "human-handoff-retailer", "unsafe-retailer")
        for project in projects:
            source = root / "examples" / "retail" / project
            run([str(executable), "retail", "validate", str(source)], cwd=outside, env=environment)
            run([str(executable), "retail", "recommend", str(source)], cwd=outside, env=environment)
            run([str(executable), "retail", "simulate", str(source), "--scenario", "lost_response"], cwd=outside, env=environment)
        negative = subprocess.run([str(executable), "retail", "simulate", str(root / "examples/retail/direct-ready"), "--scenario", "not-supported"], cwd=outside, env=environment, text=True, capture_output=True, check=False)
        if negative.returncode == 0 or "UNKNOWN_SCENARIO" not in negative.stderr:
            raise SystemExit("WHEEL_SMOKE_FAILED negative scenario did not fail closed")
    print("WHEEL_SMOKE_PASS clean wheel-only Retail workflow outside repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
