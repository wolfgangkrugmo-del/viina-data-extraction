# Reuters 2022 DEEP Search Protocol V1

## Track
Frozen completeness track under `DEEP-COMP-V1`.

Development/recovery artifacts, if later required, must be separately versioned and MUST NOT overwrite this frozen source inventory.

## Study window
2022-02-24 through 2022-12-31 inclusive.

## Source lane
- SourceID: `REUTERS`
- SourceDependenceGroup default: `DG_REUTERS`, subject to record-level dependency audit.
- Role: `CORE_DISCOVERY`.

## Search-cell design
Seven fixed search families are executed for every quarter window. Q1 begins on 2022-02-24.

1. `R1_ENERGY_REFINING` — refineries, petrochemical plants, gas-processing plants.
2. `R2_ENERGY_STORAGE_EXPORT` — oil/fuel depots, terminals, ports, export/loading infrastructure.
3. `R3_PIPELINE_PUMPING` — pipeline and pumping/compressor infrastructure.
4. `R4_DEFENSE_INDUSTRY` — weapons, ammunition, electronics, aviation, missile/UAV and other defence-industrial facilities.
5. `R5_STRATEGIC_AIR` — strategic/military air bases and fixed aviation infrastructure.
6. `R6_GRID_SUPPORT` — power plants, substations and fixed grid/support infrastructure.
7. `R7_LOGISTICS_OTHER` — other fixed strategic/logistics infrastructure within the frozen DEEP target universe.

Quarter windows:
- Q1: 2022-02-24..2022-03-31
- Q2: 2022-04-01..2022-06-30
- Q3: 2022-07-01..2022-09-30
- Q4: 2022-10-01..2022-12-31

Total fixed cells: 28.

## Mandatory contemporaneous provenance rule
Every retained named Reuters-direct source component MUST be written immediately to `output/REUTERS_2022_SOURCE_COMPONENT_MANIFEST_V1.csv` with a stable `R22S-*` ID, including at minimum:
- SearchCellID
- SourceRecordID
- Reuters article URL or stable syndicated Reuters URL
- publication date/time when recoverable
- canonical event date
- named target/location
- discovery/evidence note
- source-dependence classification

The frozen search log count MUST be computed from the manifest rows; no manually entered aggregate component count is allowed.

## Raw-hit / ledger reconciliation rule
Every retained source component must end in exactly one of:
- candidate-ledger row(s), including explicit Split/Follow-up transformations;
- documented `NON_CANDIDATE` disposition;
- documented derivative routing to another dependence group.

The source lane cannot be `PASS` unless manifest count, transformation bridge and candidate/non-candidate ledger balance exactly.

## Reuters-independent discovery rule
A Reuters item counts as a Reuters-direct discovery component only when Reuters provides original reporting, verification, imagery, industry-source reporting, operator/regional-source reporting developed within the Reuters article, or an independently identifiable Reuters chronology component.

Reuters merely relaying a Ukrainian official claim does not by itself establish independent physical effect. Such records remain candidate provenance but are coded `DEPENDENT_CONFIRMATION` or `SINGLE_SOURCE` as appropriate.

## Event rules
- Russia proper is census scope.
- Crimea/Sevastopol and other occupied Ukrainian territory remain audit-only/outside census.
- Split composite articles before dedupe.
- Same node/same attack wave is one event.
- Fresh repeat attacks remain distinct.
- Follow-up damage/repair reporting without a fresh attack is linked, not counted as a new event.
- Claim-only target reports without qualifying physical effect remain excluded or unresolved under the frozen coding rules.

## Acceptance
`SRC-2022-REUTERS` can become `PASS` only when all DEEP-COMP-V1 section 8 source-row conditions are met, including FULL_PROTOCOL coverage, dependency audit, complete candidate coding, complete dedupe, and exact source-component-to-ledger reconciliation.

`CandidateCensusComplete` remains FALSE on source rows regardless of source-lane PASS.
