# Agent Native v3.1 Canonicalization Hardening

## Root cause

The v3 security pipeline analyzed some externally supplied strings in their
encoded representation. Equivalent credential syntax could therefore reach
different decisions depending on representation: `token=FAKE`,
`token%3DFAKE`, and `token%253DFAKE` were not guaranteed to be interpreted as
the same security-relevant content.

## Required correction

v3.1 introduces one bounded `SecretCanonicalizer` beneath the existing
`SecretDetector`. It returns the original value plus at most two successive
`urllib.parse.unquote` variants, stopping early when decoding stabilizes. The
detector consumes those variants; the sanitizer and output firewall do not
decode independently.

```text
raw value -> SecretCanonicalizer -> SecretDetector
                              -> Sanitizer / AR-020 / output firewall
```

Preserving the raw variant avoids losing information while adding normalized
forms. No base64 decoding, decompression, JavaScript evaluation, HTML
recursion, or unbounded transformation is performed.

## URI handling

URI structure is still parsed with `urllib.parse`. Userinfo, path, query keys,
query values, and fragments are each passed through the shared canonical
detector before reconstruction. Unsafe URI components are replaced with
`[REDACTED]`; safe query parameters remain available for debugging where
practical.

## Bounded policy

The default maximum decode depth is two additional passes. This detects
`token%253DFAKE` while making the triple-encoded form an explicit documented
boundary rather than creating an attacker-controlled decode loop. Every pass
is bounded by a maximum input size and the transformation terminates when the
decoded value stops changing.

## Affected consumers

- AR-020 scans canonical variants through the shared detector.
- `Sanitizer.text`, nested values, and URI reconstruction use the same
  canonicalizer.
- Structured limitation resources and reasons pass through the sanitizer.
- Final JSON, Markdown, and terminal output validation scans canonical variants.

## Testing strategy

The v3.1 suite covers single, lowercase, double, and depth-bound percent
encoding; path, fragment, key-only query, nested query-value, credentialed URL,
and encoded bearer representations; cross-renderer output; canonicalization
idempotence; bounded termination; safe percent-encoded prose; and the exact
encoded limitation and AR-020 regressions.

## Deferred work

This hardening remains intentionally narrow. It does not attempt arbitrary
base64 decoding, compression expansion, script interpretation, or every
proprietary obfuscation technique. Git commit/tag traceability is a release
process requirement and is not fabricated by the scanner.

