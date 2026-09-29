# Retail Activation Blueprint

> SYNTHETIC SIMULATION — NO PRODUCTION TRANSACTION OCCURRED

Project: `direct-ready-retailer`
Project hash: `f365032d55fb29a469dd0887d4b44573686e9c7b8bc31c6b466b9508125b464f`
Pack: `sector.retail 0.1.0`

## Executive summary

| Decision bucket | Journeys |
|---|---|
| Activate now | product_discovery, controlled_checkout, cancellation |
| Pilot with controls | None |
| Use platform-mediated path | None |
| Keep human handoff | None |
| Do not activate | None |

## Business context

```json
{
  "agent_channel_priority": "conversion",
  "api_maturity": "mature",
  "business_model": "DTC",
  "business_size": "medium",
  "connector_cost_per_action": 1.0,
  "cost_ceiling_per_action": 5.0,
  "customer_identity_requirement": "optional",
  "data_sensitivity": "medium",
  "existing_platforms": [],
  "expected_agent_volume": 500,
  "human_handoff_cost_per_action": 0.0,
  "human_staff_availability": "medium",
  "inference_cost_per_action": 0.5,
  "margin_per_action": 18.0,
  "payment_requirement": "authorization",
  "protocol_platform_fee_per_action": 0.5,
  "real_time_inventory_requirement": true,
  "regulatory_sensitivity": "low",
  "reversibility": "medium",
  "technical_capacity": "high"
}
```

## Current Retail agent readiness

```json
{
  "capabilities": [
    {
      "anti_gaming_note": "declared metadata alone does not count as tested readiness",
      "capability_id": "discover",
      "counts_as_tested": true,
      "source_ref": "retail-reference",
      "state": "EXECUTABLE_IN_SIMULATION"
    },
    {
      "anti_gaming_note": "declared metadata alone does not count as tested readiness",
      "capability_id": "submit_order",
      "counts_as_tested": true,
      "source_ref": "retail-reference",
      "state": "EXECUTABLE_IN_SIMULATION"
    }
  ],
  "platforms": []
}
```

## Priority journey portfolio

```json
[
  {
    "agent_goal": "find relevant products",
    "business_goal": "qualified discovery",
    "capabilities": [
      "discover"
    ],
    "evaluation_scenarios": [
      "positive",
      "deceptive"
    ],
    "human_handoff": false,
    "journey_id": "product_discovery",
    "payment": "none",
    "persona": "shopper",
    "protocol_profiles": [
      "openapi"
    ],
    "reversibility": "high",
    "risk": "low"
  },
  {
    "agent_goal": "buy a selected item",
    "business_goal": "complete a safe sale",
    "capabilities": [
      "submit_order"
    ],
    "evaluation_scenarios": [
      "positive",
      "lost_response",
      "duplicate_retry"
    ],
    "human_handoff": false,
    "journey_id": "controlled_checkout",
    "payment": "authorization",
    "persona": "shopper",
    "protocol_profiles": [
      "openapi"
    ],
    "reversibility": "low",
    "risk": "high"
  },
  {
    "agent_goal": "cancel an eligible order",
    "business_goal": "retain trust",
    "capabilities": [
      "cancel_order"
    ],
    "evaluation_scenarios": [
      "positive",
      "cancellation_race"
    ],
    "human_handoff": false,
    "journey_id": "cancellation",
    "payment": "none",
    "persona": "customer",
    "protocol_profiles": [
      "openapi"
    ],
    "reversibility": "medium",
    "risk": "high"
  }
]
```

## Activation recommendation by journey

```json
[
  {
    "gaps": [
      {
        "description": "Define the first bounded journey and its deny conditions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Run the journey through synthetic simulation before production exposure.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Publish stable capability identifiers and explicit authorization semantics.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Provide idempotency, recovery, and receipt correlation for state-changing actions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Alternative participation paths remain viable and should be compared.",
        "field": "participation_model",
        "type": "STRATEGIC_TRADEOFF"
      }
    ],
    "journey": {
      "agent_goal": "find relevant products",
      "business_goal": "qualified discovery",
      "capabilities": [
        "discover"
      ],
      "evaluation_scenarios": [
        "positive",
        "deceptive"
      ],
      "human_handoff": false,
      "journey_id": "product_discovery",
      "payment": "none",
      "persona": "shopper",
      "protocol_profiles": [
        "openapi"
      ],
      "reversibility": "high",
      "risk": "low"
    },
    "recommendation": {
      "assumptions": [
        "Existing platforms were reported as: none.",
        "API maturity was self-described as mature; the engine does not independently verify it.",
        "The recommendation is a starting hypothesis and must be validated against executable evidence."
      ],
      "conflicts": [],
      "economic_implications": [
        "Estimated variable cost per action is 2.0000.",
        "Modeled margin per action is 18.0000.",
        "The modeled unit economics clear the configured viability boundary; validate with observed pilot data."
      ],
      "engine_version": "3b.1",
      "evidence_refs": [
        "c444d64ecb47e7293e160372c015e4dfc059ae6972d921b383710e35ea55a98f"
      ],
      "first_implementation_milestone": "Expose one bounded, low-risk direct capability with policy, idempotency, trace, and receipt evidence.",
      "generated_at": "2026-09-29T03:29:11.677347Z",
      "integration_complexity": "HIGH",
      "operating_model_implications": [
        "Own ongoing protocol, policy, and incident operations.",
        "Provide an owner for activation changes and emergency disablement."
      ],
      "overridden": false,
      "override_owner": null,
      "override_reason": null,
      "override_timestamp": null,
      "pack_hash": "5c090d3a0ee06ef054347a23cef9374931c2ed6c90c45c1d9cf2f13c273cb262",
      "pack_id": "sector.retail",
      "pack_version": "0.1.0",
      "prerequisites": [
        "Define the first bounded journey and its deny conditions.",
        "Run the journey through synthetic simulation before production exposure.",
        "Publish stable capability identifiers and explicit authorization semantics.",
        "Provide idempotency, recovery, and receipt correlation for state-changing actions."
      ],
      "rationale": [
        "The business has mature interfaces and enough technical capacity to own the agent boundary.",
        "Direct participation maximizes control when the expected volume or strategic value justifies operating it."
      ],
      "recommendation_id": "b51ed2375a954615164c4e6b",
      "recommended_pattern": "DIRECT",
      "rejected_patterns": [
        "PLATFORM_MEDIATED",
        "AGGREGATOR_MARKETPLACE",
        "DO_NOT_ACTIVATE"
      ],
      "residual_risks": [],
      "security_implications": [
        "Keep agent identity, principal authority, and business policy as separate decisions.",
        "The business owns its public agent boundary, revocation, rate limits, and recovery behavior."
      ],
      "unknowns": [],
      "viable_alternatives": [
        "HUMAN_HANDOFF"
      ]
    }
  },
  {
    "gaps": [
      {
        "description": "Define the first bounded journey and its deny conditions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Run the journey through synthetic simulation before production exposure.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Publish stable capability identifiers and explicit authorization semantics.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Provide idempotency, recovery, and receipt correlation for state-changing actions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Require explicit confirmation or stronger authority for consequential actions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Alternative participation paths remain viable and should be compared.",
        "field": "participation_model",
        "type": "STRATEGIC_TRADEOFF"
      }
    ],
    "journey": {
      "agent_goal": "buy a selected item",
      "business_goal": "complete a safe sale",
      "capabilities": [
        "submit_order"
      ],
      "evaluation_scenarios": [
        "positive",
        "lost_response",
        "duplicate_retry"
      ],
      "human_handoff": false,
      "journey_id": "controlled_checkout",
      "payment": "authorization",
      "persona": "shopper",
      "protocol_profiles": [
        "openapi"
      ],
      "reversibility": "low",
      "risk": "high"
    },
    "recommendation": {
      "assumptions": [
        "Existing platforms were reported as: none.",
        "API maturity was self-described as mature; the engine does not independently verify it.",
        "The recommendation is a starting hypothesis and must be validated against executable evidence."
      ],
      "conflicts": [],
      "economic_implications": [
        "Estimated variable cost per action is 2.0000.",
        "Modeled margin per action is 18.0000.",
        "The modeled unit economics clear the configured viability boundary; validate with observed pilot data."
      ],
      "engine_version": "3b.1",
      "evidence_refs": [
        "c444d64ecb47e7293e160372c015e4dfc059ae6972d921b383710e35ea55a98f"
      ],
      "first_implementation_milestone": "Expose one bounded, low-risk direct capability with policy, idempotency, trace, and receipt evidence.",
      "generated_at": "2026-09-29T03:29:11.677450Z",
      "integration_complexity": "HIGH",
      "operating_model_implications": [
        "Own ongoing protocol, policy, and incident operations.",
        "Provide an owner for activation changes and emergency disablement."
      ],
      "overridden": false,
      "override_owner": null,
      "override_reason": null,
      "override_timestamp": null,
      "pack_hash": "5c090d3a0ee06ef054347a23cef9374931c2ed6c90c45c1d9cf2f13c273cb262",
      "pack_id": "sector.retail",
      "pack_version": "0.1.0",
      "prerequisites": [
        "Define the first bounded journey and its deny conditions.",
        "Run the journey through synthetic simulation before production exposure.",
        "Publish stable capability identifiers and explicit authorization semantics.",
        "Provide idempotency, recovery, and receipt correlation for state-changing actions.",
        "Require explicit confirmation or stronger authority for consequential actions."
      ],
      "rationale": [
        "The business has mature interfaces and enough technical capacity to own the agent boundary.",
        "Direct participation maximizes control when the expected volume or strategic value justifies operating it."
      ],
      "recommendation_id": "a870d2d8d8f3c9b1b632804d",
      "recommended_pattern": "DIRECT",
      "rejected_patterns": [
        "PLATFORM_MEDIATED",
        "AGGREGATOR_MARKETPLACE",
        "DO_NOT_ACTIVATE"
      ],
      "residual_risks": [],
      "security_implications": [
        "Keep agent identity, principal authority, and business policy as separate decisions.",
        "The business owns its public agent boundary, revocation, rate limits, and recovery behavior."
      ],
      "unknowns": [],
      "viable_alternatives": [
        "HUMAN_HANDOFF"
      ]
    }
  },
  {
    "gaps": [
      {
        "description": "Define the first bounded journey and its deny conditions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Run the journey through synthetic simulation before production exposure.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Publish stable capability identifiers and explicit authorization semantics.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Provide idempotency, recovery, and receipt correlation for state-changing actions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Require explicit confirmation or stronger authority for consequential actions.",
        "field": "prerequisite",
        "type": "REMEDIABLE_CONTROL_GAP"
      },
      {
        "description": "Alternative participation paths remain viable and should be compared.",
        "field": "participation_model",
        "type": "STRATEGIC_TRADEOFF"
      }
    ],
    "journey": {
      "agent_goal": "cancel an eligible order",
      "business_goal": "retain trust",
      "capabilities": [
        "cancel_order"
      ],
      "evaluation_scenarios": [
        "positive",
        "cancellation_race"
      ],
      "human_handoff": false,
      "journey_id": "cancellation",
      "payment": "none",
      "persona": "customer",
      "protocol_profiles": [
        "openapi"
      ],
      "reversibility": "medium",
      "risk": "high"
    },
    "recommendation": {
      "assumptions": [
        "Existing platforms were reported as: none.",
        "API maturity was self-described as mature; the engine does not independently verify it.",
        "The recommendation is a starting hypothesis and must be validated against executable evidence."
      ],
      "conflicts": [],
      "economic_implications": [
        "Estimated variable cost per action is 2.0000.",
        "Modeled margin per action is 18.0000.",
        "The modeled unit economics clear the configured viability boundary; validate with observed pilot data."
      ],
      "engine_version": "3b.1",
      "evidence_refs": [
        "c444d64ecb47e7293e160372c015e4dfc059ae6972d921b383710e35ea55a98f"
      ],
      "first_implementation_milestone": "Expose one bounded, low-risk direct capability with policy, idempotency, trace, and receipt evidence.",
      "generated_at": "2026-09-29T03:29:11.677528Z",
      "integration_complexity": "HIGH",
      "operating_model_implications": [
        "Own ongoing protocol, policy, and incident operations.",
        "Provide an owner for activation changes and emergency disablement."
      ],
      "overridden": false,
      "override_owner": null,
      "override_reason": null,
      "override_timestamp": null,
      "pack_hash": "5c090d3a0ee06ef054347a23cef9374931c2ed6c90c45c1d9cf2f13c273cb262",
      "pack_id": "sector.retail",
      "pack_version": "0.1.0",
      "prerequisites": [
        "Define the first bounded journey and its deny conditions.",
        "Run the journey through synthetic simulation before production exposure.",
        "Publish stable capability identifiers and explicit authorization semantics.",
        "Provide idempotency, recovery, and receipt correlation for state-changing actions.",
        "Require explicit confirmation or stronger authority for consequential actions."
      ],
      "rationale": [
        "The business has mature interfaces and enough technical capacity to own the agent boundary.",
        "Direct participation maximizes control when the expected volume or strategic value justifies operating it."
      ],
      "recommendation_id": "a4e4c27d8391c4b7de96f9e5",
      "recommended_pattern": "DIRECT",
      "rejected_patterns": [
        "PLATFORM_MEDIATED",
        "AGGREGATOR_MARKETPLACE",
        "DO_NOT_ACTIVATE"
      ],
      "residual_risks": [],
      "security_implications": [
        "Keep agent identity, principal authority, and business policy as separate decisions.",
        "The business owns its public agent boundary, revocation, rate limits, and recovery behavior."
      ],
      "unknowns": [],
      "viable_alternatives": [
        "HUMAN_HANDOFF"
      ]
    }
  }
]
```

## Architecture options

```json
[
  "DIRECT",
  "PLATFORM_MEDIATED",
  "AGGREGATOR_MARKETPLACE",
  "HUMAN_HANDOFF"
]
```

## Protocol/profile readiness

```json
[
  {
    "language": "profile mapped; certification not claimed",
    "profile_id": "retail.openapi.reference",
    "status": "FIXTURE_VALIDATED"
  }
]
```

## Simulation results

```json
[
  {
    "input_hash": "a978a776c1eed793d1db7824b884adcbc2466d832fd42b9a3734e9f8cdb118dc",
    "result": {
      "findings": [],
      "message": "order accepted",
      "order": {
        "amount": 49.99,
        "currency": "USD",
        "order_id": "order-1e757dfdadea7885e71ad00d",
        "principal_id": "principal:demo",
        "product_id": "prod:direct",
        "quantity": 1,
        "state": "ORDER_ACCEPTED",
        "trace_id": "49aaed3b010e416bb2b52b6b1b68f582",
        "variant_id": "variant:default"
      },
      "receipt": {
        "agent_id": "agent:demo",
        "business_id": "merchant:direct-ready",
        "capability_id": "sector.retail:submit_order",
        "confirmation_reference": "confirmation-57ae138772460887db2bd679",
        "correlation_id": "retail:sim-happy",
        "currency": "USD",
        "decision": "ALLOW",
        "delegation_reference": "retail-reference-delegation",
        "environment": "SANDBOX",
        "evidence_refs": [
          "order:order-1e757dfdadea7885e71ad00d",
          "quote:quote-da093dd8a9ce4391dbb63708"
        ],
        "integrity": "sha256:0247fb30a2cf23fb24bc42c3e458653eeff17f140ba16eccafd1430b25723056",
        "policy_id": "retail-reference-policy",
        "policy_version": "retail-0.1",
        "principal_reference": "principal:demo",
        "provider_id": "provider:demo",
        "quote_reference": "quote-da093dd8a9ce4391dbb63708",
        "receipt_id": "receipt-1da6778dcb2b4cafbb16197a",
        "request_hash": "6a14269445e431a5d010055d185c75c94be8a7b25a8ed50c973e9d91dc7530cf",
        "resource_reference": "prod:direct:variant:default",
        "result": "ORDER_ACCEPTED",
        "side_effect": "IRREVERSIBLE",
        "timestamp": "2026-09-29T03:29:11.680617Z",
        "trace_id": "49aaed3b010e416bb2b52b6b1b68f582",
        "value": 49.99
      },
      "replayed": false,
      "state": "ORDER_ACCEPTED",
      "status": "ORDER_ACCEPTED",
      "trace": {
        "correlation_id": "retail:sim-happy",
        "events": [
          {
            "attributes": {
              "confirmation_id": "confirmation-57ae138772460887db2bd679"
            },
            "correlation_id": "retail:sim-happy",
            "name": "confirmation_received",
            "span_id": "1f62eae38a624cf6",
            "timestamp": "2026-09-29T03:29:11.680573Z",
            "trace_id": "49aaed3b010e416bb2b52b6b1b68f582"
          },
          {
            "attributes": {
              "logical_transaction_id": "txn-ec608d4d5c09f9b464097ce4",
              "quote_id": "quote-da093dd8a9ce4391dbb63708"
            },
            "correlation_id": "retail:sim-happy",
            "name": "checkout_submitted",
            "span_id": "c7c4c66c900b4132",
            "timestamp": "2026-09-29T03:29:11.680585Z",
            "trace_id": "49aaed3b010e416bb2b52b6b1b68f582"
          },
          {
            "attributes": {
              "order_id": "order-1e757dfdadea7885e71ad00d"
            },
            "correlation_id": "retail:sim-happy",
            "name": "order_accepted",
            "span_id": "a41f0bedf6de4953",
            "timestamp": "2026-09-29T03:29:11.680727Z",
            "trace_id": "49aaed3b010e416bb2b52b6b1b68f582"
          }
        ],
        "otel": {
          "resourceSpans": [
            {
              "scopeSpans": [
                {
                  "spans": [
                    {
                      "attributes": [
                        {
                          "key": "confirmation_id",
                          "value": {
                            "stringValue": "confirmation-57ae138772460887db2bd679"
                          }
                        }
                      ],
                      "events": [
                        {
                          "name": "confirmation_received",
                          "time": "2026-09-29T03:29:11.680573Z"
                        }
                      ],
                      "name": "confirmation_received",
                      "spanId": "1f62eae38a624cf6",
                      "startTime": "2026-09-29T03:29:11.680573Z",
                      "traceId": "49aaed3b010e416bb2b52b6b1b68f582"
                    },
                    {
                      "attributes": [
                        {
                          "key": "logical_transaction_id",
                          "value": {
                            "stringValue": "txn-ec608d4d5c09f9b464097ce4"
                          }
                        },
                        {
                          "key": "quote_id",
                          "value": {
                            "stringValue": "quote-da093dd8a9ce4391dbb63708"
                          }
                        }
                      ],
                      "events": [
                        {
                          "name": "checkout_submitted",
                          "time": "2026-09-29T03:29:11.680585Z"
                        }
                      ],
                      "name": "checkout_submitted",
                      "spanId": "c7c4c66c900b4132",
                      "startTime": "2026-09-29T03:29:11.680585Z",
                      "traceId": "49aaed3b010e416bb2b52b6b1b68f582"
                    },
                    {
                      "attributes": [
                        {
                          "key": "order_id",
                          "value": {
                            "stringValue": "order-1e757dfdadea7885e71ad00d"
                          }
                        }
                      ],
                      "events": [
                        {
                          "name": "order_accepted",
                          "time": "2026-09-29T03:29:11.680727Z"
                        }
                      ],
                      "name": "order_accepted",
                      "spanId": "a41f0bedf6de4953",
                      "startTime": "2026-09-29T03:29:11.680727Z",
                      "traceId": "49aaed3b010e416bb2b52b6b1b68f582"
                    }
                  ]
                }
              ]
            }
          ]
        },
        "trace_id": "49aaed3b010e416bb2b52b6b1b68f582"
      }
    },
    "result_hash": "1b56091cb8f3efc749f50cfa2c74d468e7813232aa69c551dfafb0d010dfc363",
    "scenario": "happy-path",
    "scenario_version": "1.0",
    "seed": 42,
    "synthetic_boundary": "SYNTHETIC SIMULATION \u2014 NO PRODUCTION TRANSACTION OCCURRED"
  },
  {
    "input_hash": "856f0355f9fdb0fbba56047e84f044e601afc49542d3759574e03727b74f9e5d",
    "result": {
      "first": {
        "findings": [
          "UNKNOWN_OUTCOME"
        ],
        "message": "downstream order succeeded but response was lost",
        "order": {
          "amount": 49.99,
          "currency": "USD",
          "order_id": "order-6058ef75c7d95e7a465be524",
          "principal_id": "principal:demo",
          "product_id": "prod:direct",
          "quantity": 1,
          "state": "UNKNOWN_OUTCOME",
          "trace_id": "2c7b0c856c2942a08788a2ce225816c9",
          "variant_id": "variant:default"
        },
        "receipt": {
          "agent_id": "agent:demo",
          "business_id": "merchant:direct-ready",
          "capability_id": "sector.retail:submit_order",
          "confirmation_reference": "confirmation-57ae138772460887db2bd679",
          "correlation_id": "retail:sim-retry",
          "currency": "USD",
          "decision": "ALLOW",
          "delegation_reference": "retail-reference-delegation",
          "environment": "SANDBOX",
          "evidence_refs": [
            "order:order-6058ef75c7d95e7a465be524",
            "quote:quote-da093dd8a9ce4391dbb63708"
          ],
          "integrity": "sha256:9da61cc41eee2bda7910a70df7172656ee105626e83c479cffdd59d38672cedc",
          "policy_id": "retail-reference-policy",
          "policy_version": "retail-0.1",
          "principal_reference": "principal:demo",
          "provider_id": "provider:demo",
          "quote_reference": "quote-da093dd8a9ce4391dbb63708",
          "receipt_id": "receipt-712f102926544ab88db2564c",
          "request_hash": "6a14269445e431a5d010055d185c75c94be8a7b25a8ed50c973e9d91dc7530cf",
          "resource_reference": "prod:direct:variant:default",
          "result": "ORDER_ACCEPTED",
          "side_effect": "IRREVERSIBLE",
          "timestamp": "2026-09-29T03:29:11.683793Z",
          "trace_id": "2c7b0c856c2942a08788a2ce225816c9",
          "value": 49.99
        },
        "replayed": false,
        "state": "UNKNOWN_OUTCOME",
        "status": "UNKNOWN_OUTCOME",
        "trace": {
          "correlation_id": "retail:sim-retry",
          "events": [
            {
              "attributes": {
                "confirmation_id": "confirmation-57ae138772460887db2bd679"
              },
              "correlation_id": "retail:sim-retry",
              "name": "confirmation_received",
              "span_id": "d8293034cb874be6",
              "timestamp": "2026-09-29T03:29:11.683763Z",
              "trace_id": "2c7b0c856c2942a08788a2ce225816c9"
            },
            {
              "attributes": {
                "logical_transaction_id": "txn-58667592ba89a80950c41926",
                "quote_id": "quote-da093dd8a9ce4391dbb63708"
              },
              "correlation_id": "retail:sim-retry",
              "name": "checkout_submitted",
              "span_id": "c7cb0eb685d54e77",
              "timestamp": "2026-09-29T03:29:11.683770Z",
              "trace_id": "2c7b0c856c2942a08788a2ce225816c9"
            },
            {
              "attributes": {
                "order_id": "order-6058ef75c7d95e7a465be524"
              },
              "correlation_id": "retail:sim-retry",
              "name": "order_accepted",
              "span_id": "fbb8b1e12ee34d40",
              "timestamp": "2026-09-29T03:29:11.683886Z",
              "trace_id": "2c7b0c856c2942a08788a2ce225816c9"
            },
            {
              "attributes": {
                "order_id": "order-6058ef75c7d95e7a465be524"
              },
              "correlation_id": "retail:sim-retry",
              "name": "unknown_outcome",
              "span_id": "374d17a817e0465a",
              "timestamp": "2026-09-29T03:29:11.683894Z",
              "trace_id": "2c7b0c856c2942a08788a2ce225816c9"
            }
          ],
          "otel": {
            "resourceSpans": [
              {
                "scopeSpans": [
                  {
                    "spans": [
                      {
                        "attributes": [
                          {
                            "key": "confirmation_id",
                            "value": {
                              "stringValue": "confirmation-57ae138772460887db2bd679"
                            }
                          }
                        ],
                        "events": [
                          {
                            "name": "confirmation_received",
                            "time": "2026-09-29T03:29:11.683763Z"
                          }
                        ],
                        "name": "confirmation_received",
                        "spanId": "d8293034cb874be6",
                        "startTime": "2026-09-29T03:29:11.683763Z",
                        "traceId": "2c7b0c856c2942a08788a2ce225816c9"
                      },
                      {
                        "attributes": [
                          {
                            "key": "logical_transaction_id",
                            "value": {
                              "stringValue": "txn-58667592ba89a80950c41926"
                            }
                          },
                          {
                            "key": "quote_id",
                            "value": {
                              "stringValue": "quote-da093dd8a9ce4391dbb63708"
                            }
                          }
                        ],
                        "events": [
                          {
                            "name": "checkout_submitted",
                            "time": "2026-09-29T03:29:11.683770Z"
                          }
                        ],
                        "name": "checkout_submitted",
                        "spanId": "c7cb0eb685d54e77",
                        "startTime": "2026-09-29T03:29:11.683770Z",
                        "traceId": "2c7b0c856c2942a08788a2ce225816c9"
                      },
                      {
                        "attributes": [
                          {
                            "key": "order_id",
                            "value": {
                              "stringValue": "order-6058ef75c7d95e7a465be524"
                            }
                          }
                        ],
                        "events": [
                          {
                            "name": "order_accepted",
                            "time": "2026-09-29T03:29:11.683886Z"
                          }
                        ],
                        "name": "order_accepted",
                        "spanId": "fbb8b1e12ee34d40",
                        "startTime": "2026-09-29T03:29:11.683886Z",
                        "traceId": "2c7b0c856c2942a08788a2ce225816c9"
                      },
                      {
                        "attributes": [
                          {
                            "key": "order_id",
                            "value": {
                              "stringValue": "order-6058ef75c7d95e7a465be524"
                            }
                          }
                        ],
                        "events": [
                          {
                            "name": "unknown_outcome",
                            "time": "2026-09-29T03:29:11.683894Z"
                          }
                        ],
                        "name": "unknown_outcome",
                        "spanId": "374d17a817e0465a",
                        "startTime": "2026-09-29T03:29:11.683894Z",
                        "traceId": "2c7b0c856c2942a08788a2ce225816c9"
                      }
                    ]
                  }
                ]
              }
            ]
          },
          "trace_id": "2c7b0c856c2942a08788a2ce225816c9"
        }
      }
    },
    "result_hash": "32a1236c8fae7adf53a0b729e171f42524f3203004e219eb184fc761d147762f",
    "scenario": "lost-response",
    "scenario_version": "1.0",
    "seed": 42,
    "synthetic_boundary": "SYNTHETIC SIMULATION \u2014 NO PRODUCTION TRANSACTION OCCURRED"
  },
  {
    "input_hash": "13ee7ef3b2db66d660c4edd806d1bd470ce34aa79e87b2f01ebe665ee3bcdf11",
    "result": {
      "findings": [
        "UNKNOWN_AGENT_PURCHASE"
      ],
      "message": "unknown agent cannot purchase",
      "replayed": false,
      "state": "ORDER_REJECTED",
      "status": "DENIED",
      "trace": {
        "correlation_id": "retail:sim-denied",
        "events": [
          {
            "attributes": {
              "reason": "unknown_agent"
            },
            "correlation_id": "retail:sim-denied",
            "name": "retail_order_denied",
            "span_id": "a22d3f277f304087",
            "timestamp": "2026-09-29T03:29:11.686627Z",
            "trace_id": "f8c08f2040114902b52729794a70d09e"
          }
        ],
        "otel": {
          "resourceSpans": [
            {
              "scopeSpans": [
                {
                  "spans": [
                    {
                      "attributes": [
                        {
                          "key": "reason",
                          "value": {
                            "stringValue": "unknown_agent"
                          }
                        }
                      ],
                      "events": [
                        {
                          "name": "retail_order_denied",
                          "time": "2026-09-29T03:29:11.686627Z"
                        }
                      ],
                      "name": "retail_order_denied",
                      "spanId": "a22d3f277f304087",
                      "startTime": "2026-09-29T03:29:11.686627Z",
                      "traceId": "f8c08f2040114902b52729794a70d09e"
                    }
                  ]
                }
              ]
            }
          ]
        },
        "trace_id": "f8c08f2040114902b52729794a70d09e"
      }
    },
    "result_hash": "31abe80de02471970fd08cf1fc099d88408df27d4df864224df6833a307743d2",
    "scenario": "unknown-agent",
    "scenario_version": "1.0",
    "seed": 42,
    "synthetic_boundary": "SYNTHETIC SIMULATION \u2014 NO PRODUCTION TRANSACTION OCCURRED"
  }
]
```

## Operating model

```json
{
  "human_control": "bounded confirmation and handoff",
  "owner": "retailer",
  "production_status": "not evaluated"
}
```

## 30/60/90-day roadmap

```json
{
  "cancellation": [
    {
      "actions": [
        "Close evidence gaps",
        "Select one bounded priority journey",
        "Confirm ownership, policy, and controlled fixtures"
      ],
      "window": "days_1_30"
    },
    {
      "actions": [
        "Validate the DIRECT path in sandbox",
        "Operationalize monitoring, handoff, and reconciliation",
        "Run acceptance tests"
      ],
      "window": "days_31_60"
    },
    {
      "actions": [
        "Run a bounded pilot",
        "Measure outcomes and support burden",
        "Decide whether to expand, mediate, or stop"
      ],
      "window": "days_61_90"
    }
  ],
  "controlled_checkout": [
    {
      "actions": [
        "Close evidence gaps",
        "Select one bounded priority journey",
        "Confirm ownership, policy, and controlled fixtures"
      ],
      "window": "days_1_30"
    },
    {
      "actions": [
        "Validate the DIRECT path in sandbox",
        "Operationalize monitoring, handoff, and reconciliation",
        "Run acceptance tests"
      ],
      "window": "days_31_60"
    },
    {
      "actions": [
        "Run a bounded pilot",
        "Measure outcomes and support burden",
        "Decide whether to expand, mediate, or stop"
      ],
      "window": "days_61_90"
    }
  ],
  "product_discovery": [
    {
      "actions": [
        "Close evidence gaps",
        "Select one bounded priority journey",
        "Confirm ownership, policy, and controlled fixtures"
      ],
      "window": "days_1_30"
    },
    {
      "actions": [
        "Validate the DIRECT path in sandbox",
        "Operationalize monitoring, handoff, and reconciliation",
        "Run acceptance tests"
      ],
      "window": "days_31_60"
    },
    {
      "actions": [
        "Run a bounded pilot",
        "Measure outcomes and support burden",
        "Decide whether to expand, mediate, or stop"
      ],
      "window": "days_61_90"
    }
  ]
}
```

## Assumptions and unknowns

```json
[]
```

## Residual risks

```json
[]
```

## Evidence index

```json
[
  "c444d64ecb47e7293e160372c015e4dfc059ae6972d921b383710e35ea55a98f"
]
```
