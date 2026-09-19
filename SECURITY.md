# Security Policy

Agent Native is security-adjacent software that fetches and parses untrusted content. Use it only against systems you own or are authorized to assess. Anonymous scans are passive and bounded.

Do not include credentials, customer data, or undisclosed exploitable details in public issues. Report security-sensitive findings privately to the project maintainers with reproduction steps, affected version, and impact. Findings about scanned third parties are not automatically published.

The v0.1 CLI blocks private, loopback, link-local, multicast, reserved, and metadata-style destinations for network acquisition, rejects URL credentials, validates redirect targets, and never executes fetched content.
