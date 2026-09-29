from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "V3" / "evidence" / "phase3b_closure_builder_manifest.json"
VERIFIER = ROOT / "scripts" / "verify_phase3b_evidence.py"


def run_verifier(manifest: dict[str, object], name: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"phase3b-evidence-{name}-") as directory:
        path = Path(directory) / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(VERIFIER), str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    return {
        "case": name,
        "returncode": completed.returncode,
        "accepted": completed.returncode == 0,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def main() -> int:
    base = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases: list[tuple[str, dict[str, object]]] = []

    missing_artifact = deepcopy(base)
    missing_artifact["artifacts"][0]["path"] = "V3/does-not-exist.md"
    cases.append(("missing_required_artifact", missing_artifact))

    no_artifacts = deepcopy(base)
    no_artifacts.pop("artifacts", None)
    cases.append(("artifacts_array_removed", no_artifacts))

    nonexistent_with_digest = deepcopy(base)
    nonexistent_with_digest["artifacts"] = [{"path": "missing.bin", "sha256": "0" * 64}]
    cases.append(("nonexistent_artifact_with_digest", nonexistent_with_digest))

    arbitrary_shas = deepcopy(base)
    arbitrary_shas["source_commit_sha"] = "1" * 40
    arbitrary_shas["evidence_commit_sha"] = "2" * 40
    arbitrary_shas["reviewed_commit_sha"] = "3" * 40
    cases.append(("arbitrary_unequal_commit_shas", arbitrary_shas))

    fabricated_ci = deepcopy(base)
    fabricated_ci["ci"]["run_id"] = "99999999999"
    fabricated_ci["ci"]["url"] = "https://github.com/revanthpp/agent-native/actions/runs/99999999999"
    cases.append(("fabricated_ci_run", fabricated_ci))

    results = [run_verifier(manifest, name) for name, manifest in cases]
    print(json.dumps(results, indent=2))
    return 1 if any(item["accepted"] for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
