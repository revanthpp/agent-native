"""Bind a builder manifest to the completed GitHub run and uploaded artifact."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from verify_phase3b_evidence import GitHubAPI, verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-id", type=int, required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--artifact-url", required=True)
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--repository")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    api = GitHubAPI()
    repository = args.repository or os.environ.get("GITHUB_REPOSITORY", "revanthpp/agent-native")
    run_id = args.run_id or int(os.environ["GITHUB_RUN_ID"])
    run = api.run(repository, run_id)
    artifacts = api.artifacts(repository, run_id).get("artifacts", [])
    uploaded = next((item for item in artifacts if item.get("id") == args.artifact_id), None)
    if uploaded is None:
        raise SystemExit("GATE2_FINALIZE_FAILED uploaded artifact is not attached to this run")
    github_digest = str(uploaded.get("digest", "")).removeprefix("sha256:")
    claimed_digest = args.artifact_digest.removeprefix("sha256:")
    if github_digest != claimed_digest:
        raise SystemExit("GATE2_FINALIZE_FAILED action output digest does not match GitHub API digest")
    manifest["ci"] = {"repository": repository, "run_id": run_id, "run_attempt": int(run.get("run_attempt") or os.environ.get("GITHUB_RUN_ATTEMPT", "1")), "workflow_path": run.get("path"), "event": run.get("event"), "head_sha": run.get("head_sha"), "status": run.get("status"), "conclusion": run.get("conclusion"), "created_at": run.get("created_at"), "started_at": run.get("run_started_at"), "completed_at": run.get("updated_at"), "url": run.get("html_url"), "uploaded_artifact": {"id": args.artifact_id, "name": uploaded.get("name"), "digest": github_digest, "url": args.artifact_url}}
    temporary = args.manifest.with_name(f".{args.manifest.name}.finalize")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(args.manifest)
    result = verify_manifest(args.manifest, repo_root=Path(__file__).resolve().parents[1], offline=False, github=api)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "EVIDENCE_VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
