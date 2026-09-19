# Data Handling

The v0.1 CLI keeps fetched artifacts in memory for the duration of a scan and emits only bounded evidence fragments in reports. Evidence is redacted before serialization. Do not scan with credentials or sensitive data. Future private/staging modes must use tenant isolation, ephemeral credentials, configurable retention, and explicit deletion.
