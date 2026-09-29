from __future__ import annotations

import sys
import zipfile
from pathlib import Path


def verify(path: str) -> bool:
    artifact = Path(path)
    names = zipfile.ZipFile(artifact).namelist()
    legacy_modules = {
        "agentnative/v2core.py",
        "agentnative/policy.py",
        "agentnative/identity.py",
        "agentnative/ownership.py",
        "agentnative/delegation.py",
    }
    bad = [name for name in names if "agentnative_v2" in name or name.startswith("v2/src/") or name in legacy_modules]
    runtime = [name for name in names if name.startswith("agentnative/")]
    if bad or not runtime:
        print(f"PACKAGE_CONTENT_INVALID bad={bad} runtime_files={len(runtime)}")
        return False
    print(f"PACKAGE_CONTENT_VALID runtime_files={len(runtime)}")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if verify(sys.argv[1]) else 1)
