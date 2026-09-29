# Remote Ref Results

Independent checks passed for:

- valid same-origin nested remote refs;
- provenance/content hash for each referenced artifact;
- localhost block without fetch;
- RFC1918 block without fetch;
- link-local block without fetch;
- IPv6 loopback block without fetch;
- `file://` unsupported-scheme block without fetch;
- `ftp://` unsupported-scheme block without fetch;
- cross-origin redirect block.

Existing root tests also cover local refs, same-origin redirects through `SafeFetcher`, cycle detection, depth limits, document-count limits, fetch failures, timeouts, oversized bodies, malformed remote docs, and nested-ref provenance.

Open finding: malicious YAML object tags are safe from execution but not cleanly converted to a structured adapter error by direct OpenAPI adapter APIs.
