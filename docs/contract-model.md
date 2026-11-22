# Contract model

Each operation o of the Building OS northbound interface has a contract C(o) = ⟨Pre, Post, Fail, T⟩:
preconditions, postconditions, required behaviour on failure, and timing/time-semantics conditions. The suite
`bos-contract-suite-v0` ([data file](../src/bos_contract_testbed/data/bos-contract-suite.yaml)) splits the cells for
five operations into 35 atomic conditions.

| Operation | covered | partial | gap | conflict |
|---|---|---|---|---|
| telemetry_read | 3 | 1 | 2 | 1 |
| time | 3 | 1 | 2 | 0 |
| control_write | 8 | 2 | 0 | 1 |
| release | 4 | 0 | 1 | 0 |
| authorized_query | 3 | 3 | 0 | 0 |
| **total** | **21** | **7** | **5** | **2** |

`conflict` means a test exists but asserts the opposite of the condition. For example, RI accepts a valueless frame as
0.0 for backward compatibility, and RI's control-schema failure policy defaults to allow. These counts are asserted by
`tests/offline/test_contract_suite.py`.

## Layers

A trace is judged per condition. A *flag* is either an observed refusal or a violation. Layers are cumulative.

| Layer | Conditions | Needs to observe |
|---|---|---|
| V0 | S: non-2xx where 2xx was expected; 202 without `controlId`; TelemetryReading envelope fields and types | northbound replies only |
| V1 | `pre-id-space`, `pre-write-permission`, `fail-out-of-range-refused`, `t-invalid-release-value`, `t-schema-missing` | registered ids, token kind, ControlSchema, policy |
| V2 | `post-origin-and-quality`, `post-observation-time`, `fail-quality-refusable`, `post-readback`, `post-default-readback`, `post-actor-result-recorded` | row metadata, history, readback, southbound priority array, audit rows |
| V3 | `post-unit`, `fail-missing-not-filled`, `fail-unverifiable-refused`, `fail-release-failure-reported` | Point units, missing-value markers, removed schema fields, post-release array |

An injection is *detected at Vk* when any condition of Vk flags its trace. A control trace in which Safety refused
before RI is **Not Tested**, not undetected.

## Trace shapes

```text
telemetry: {kind: "telemetry", registered: [id],
            sent:  [{point_id, timestamp, value|null, attributes, accepted, missing?}],
            reads: [{api: latest|history, point_id, status, rows: [TelemetryReading]}],
            id_space_reads?: bool, units?: {point_id: unit}}
control:   {kind: "control", point_id, schema: {min, max} | {enum: [...]} | null, policy: allow|deny,
            requests: [{op: write|release, token: writer|reader|none, value, reached_ri, status, body}],
            readback: {expected, observed: [...]} | null, audit: {accepted, rows} | null,
            release_after: {priority_array[16], present_value, relinquish_default} | null,
            schema_removed?: [dataType|minValue|maxValue]}
```

## Lifecycle scenario 4 (B13)

Priority 8 (BDE) is released while a second writer holds priority 16.

- **E1**: before the release, priority 8 holds BDE's last value, priority 16 holds the second writer's value, and the present value equals priority 8.
- **E2**: after the release, priority 8 is empty and the present value equals the priority-16 value, not the relinquish default.
- **E5**: after the second writer relinquishes, the array is empty and the present value is the default.

A missing or failed read leaves its expectation `None` (Not Tested), never False.
