# Architecture

## Systems under test (not in this repository)

```
BOPTEST / hvac-sim plant ──BACnet──▶ Nexus Gateway ──gRPC/mTLS──▶ Building OS RI ◀──HTTP── BDE (Safety Runtime writes)
        ▲                                                                ▲
        └──────────── testbed: single time controller, Oracle/KPI, read-only southbound probes ──────────────┘
```

| System | Responsibility |
|---|---|
| BOPTEST / hvac-sim | physical simulation, BACnet virtual plant, KPI |
| Nexus Gateway | device connection, address resolution, point mapping, telemetry normalisation, executing permitted commands |
| Building OS RI | canonical Point IDs and Point List, digital twin, storage, authorisation, control API |
| BDE | prediction, optimisation, control policy; its Safety Runtime alone may write through RI |
| Integration testbed (private) | scenarios, single time advance, Oracle/KPI, cross-system verification |

Invariants the experiments relied on: BDE never talks to BOPTEST or BACnet directly. Writes go only through the Safety
Runtime and RI. Oracle data stays out of BDE's normal paths. Each simulation has one time controller.

## This repository

This repository holds only the **judging** part of that testbed:

```
trace (JSON) ──▶ checks.s_flags / checks.c_flags ──▶ layers.judge_layers (V0–V2) ──▶ v3.judge (V0–V3)
priority reads ──▶ lifecycle.judge (E1, E2, E5) ──▶ lifecycle.scenario
suite YAML ──▶ suite.structural_problems / suite.summarize
```

- Inputs are plain JSON traces (shapes in [contract-model.md](contract-model.md)). No I/O to any system.
- `checks.py` is a byte-identical copy of the original predicates. The other modules keep the original logic. Only
  imports and artifact loading were changed.
- `results/` holds what was observed, with the status from the original reports. The predicates do not regenerate
  those numbers.
