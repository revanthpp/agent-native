# Protocol Adapter Results

The common adapter contract exposes:

| Adapter | detect | parse | validate | normalize | capabilities | auth | actions | errors | limitations |
|---|---|---|---|---|---|---|---|---|---|
| OpenAPI | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| MCP | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| A2A | yes | yes | yes | yes | yes | yes | yes | yes | yes |
| IndependentDummyAdapter | yes | yes | yes | yes | yes | yes | yes | yes | yes |

Independent extension adapter registration worked through `AdapterRegistry.register`/constructor injection without modifying built-in adapter source. Failure isolation worked: a throwing dummy adapter produced an `ADAPTER_FAILURE` result instead of crashing the registry.

Finding: direct OpenAPI adapter calls are not fully fail-closed for malicious YAML constructor tags. The registry contains the failure, but `OpenAPIAdapter.detect()` and `.parse()` raise `ConstructorError` directly.
