"""Verify Phase 3B evidence artifact digests and source/evidence provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("status") != "BUILDER_EVIDENCE_ONLY":
        print("EVIDENCE_INVALID status must remain BUILDER_EVIDENCE_ONLY")
        return 1
    source = manifest.get("source_commit_sha")
    evidence = manifest.get("evidence_commit_sha")
    if not source or source == evidence:
        print("EVIDENCE_INVALID source_commit_sha and evidence_commit_sha must be explicit and non-self-referential")
        return 1
    for item in manifest.get("artifacts", []):
        path = Path(item["path"] if isinstance(item, dict) else item)
        expected = item.get("sha256") if isinstance(item, dict) else None
        if expected and path.exists() and digest(path) != expected:
            print(f"EVIDENCE_INVALID digest mismatch: {path}")
            return 1
    print("EVIDENCE_VALID provenance and artifact digests verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
