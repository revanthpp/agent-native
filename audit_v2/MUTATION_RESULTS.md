# Mutation Results

`PYTHONPATH=src .audit-env/bin/python scripts/run_phase2b_mutations.py` returned success.

The script now mutates production seams through `AuthorizationControls`, `DelegationControls`, `PolicyControls`, sanitizer configuration, and OpenAPI network-policy injection.

Claim reproduced:

- 17 total mutation cases.
- 17 caught.

Covered controls include owner verification, signature verification, replay protection, grant expiry, revocation, principal/agent/provider/audience/capability/resource/value binding, explicit deny precedence, default deny, policy version, secret redaction, and remote `$ref` network policy.

I did not perform source-rewriting mutation experiments in this run because the injectable production controls now directly exercise the seams that were previously fake-lambda evidence.
