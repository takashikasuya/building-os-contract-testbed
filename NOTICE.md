# Notice

**Copyright holder: to be confirmed** (see [docs/publication-audit.md](docs/publication-audit.md) §4).
Code is licensed under the Apache License 2.0 ([LICENSE](LICENSE)). Documentation, results, fixtures and the contract
suite data are licensed under CC-BY-4.0 ([LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt)). See the README for the
file-level split. The third-party names below are not covered by either license.

## Origin

The predicates, unit tests and reports were exported from a private integration testbed at commit
`e7e020dfa9ecf1df5afbcb555b84f3f055473943`. File-level provenance is in [public-export.yaml](public-export.yaml)
and [release/export-provenance.json](release/export-provenance.json).

## Third-party names

The names below identify the systems the experiments were run against. This repository contains none of their code.
It cites some of their test identifiers (names only) in the contract suite.

| Name | Owner / location | License |
|---|---|---|
| BOPTEST (`project1-boptest`) | IBPSA Project 1, github.com/ibpsa/project1-boptest | not verified for this release |
| Building OS RI (`gutp-building-os-ri`) | github.com/gutp-bim/gutp-building-os-ri | no license detected by GitHub; not verified |
| Nexus Gateway | github.com/gutp-bim/nexus-gateway | not verified |
| SBCO Data Model Builder | github.com/smartbuilding-co-creation-organization/smartbuilding_datamodel_builder | not verified |
| BDE (building-decision-engine), hvac-sim, tenant-portal | private repositories | not public |

## Dependencies

| Package | Use | License (as declared by the package) |
|---|---|---|
| PyYAML | runtime | MIT |
| pytest | tests only | MIT |
