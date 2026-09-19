from __future__ import annotations

import sys
from pathlib import Path


def verify_repository(root: Path) -> bool:
    required = [root / "src/agentnative", root / "pyproject.toml", root / "tests", root / "evals"]
    if not all(path.exists() for path in required):
        return False
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    return 'name = "agentnative"' in text and 'agentnative = "agentnative.cli.main:main"' in text


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if not verify_repository(root):
        print("QA_ABORTED_WRONG_REPOSITORY")
        return 1
    print("QA_REPOSITORY_IDENTITY_CONFIRMED: Agent Native")
    return 0


if __name__ == "__main__":
    sys.exit(main())
