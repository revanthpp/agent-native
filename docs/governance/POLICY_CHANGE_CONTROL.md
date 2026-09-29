# Policy Change Control

Production policy rules require an owner and version. Decisions are deterministic for the same policy version, identity, delegation, capability, resource, environment, and context. State-changing actions default to deny. Policy linting flags missing secure defaults, wildcard allows, duplicate/contradictory selectors, unowned rules, expired rules, and high-risk allows without confirmation.
