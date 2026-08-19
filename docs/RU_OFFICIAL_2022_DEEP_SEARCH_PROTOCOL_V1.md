# RU_OFFICIAL 2022 DEEP Search Protocol V1

## Track
Frozen completeness track under `DEEP-COMP-V1`.

## Study window
2022-02-24 through 2022-12-31 inclusive.

## Source lane
- SourceID: `RU_OFFICIAL`
- SourceDependenceGroup: `DG_RU_OFFICIAL`
- Role: `SUPPLEMENTAL_DISCOVERY`
- AccessStatus: `AVAILABLE`

## Purpose
This lane has two simultaneous functions:
1. independent/supplemental full-window discovery for C2/C6;
2. primary-source adjudication of unresolved actor, target, node and physical-effect fields in the merged 2022 candidate register.

It MUST NOT be limited to the five known Reuters C5 residuals. A targeted-only pass cannot satisfy FULL_PROTOCOL or count toward C2/C6.

## Required source classes
Search and archive applicable public records from:
- regional governors / regional administrations in Russia-proper border and deep-strike regions;
- Russian Ministry of Defence;
- Russian Investigative Committee;
- Ministry of Emergency Situations / regional emergency services;
- operators and state infrastructure entities when acting as primary facility sources (e.g. grid, pipeline, fuel/storage operators);
- other Russian federal/regional official releases where they are the originating source for an event-level claim.

Derivative media copies may be used only to recover the text/URL of a primary statement; they do not create an additional dependence group.

## Full-protocol search structure
Run monthly windows from 2022-02-24 through 2022-12-31 against all seven frozen DEEP target families:
1. R1_ENERGY_REFINING
2. R2_ENERGY_STORAGE_EXPORT
3. R3_PIPELINE_PUMPING
4. R4_DEFENSE_INDUSTRY
5. R5_STRATEGIC_AIR
6. R6_GRID_SUPPORT
7. R7_LOGISTICS_OTHER

Every month×family cell must be explicitly COMPLETED, including zero-yield cells.

## Mandatory source inventory
Every retained official event component must receive a stable `RU22S-*` identifier in `output/RU_OFFICIAL_2022_SOURCE_COMPONENT_MANIFEST_V1.csv` at discovery time, with:
- SearchCellID
- originating authority/operator
- originating URL or archived primary-source reference
- publication date/time when available
- canonical event date
- target/location
- event/attribution statement
- dependence classification
- candidate/non-candidate disposition status

Aggregate-only counts are prohibited.

## Candidate and reconciliation rules
- Russia proper is census scope.
- Crimea/Sevastopol and occupied Ukrainian territory are audit-only/outside census.
- Split composite releases before dedupe.
- Cross-lane matches to VIINA/Reuters are linked, not counted again.
- A newly discovered valid Russia-proper event remains a new candidate even if absent from both core lanes.
- Claim-only reports remain explicit candidates or exclusions according to DEEP-COMP-V1 event/effect rules.
- All official-source records must preserve the distinction between an authority confirming a physical effect and an authority attributing responsibility.

## C5 adjudication safeguard
The five currently FORMALLY_UNDECIDABLE 2022 core candidates may be re-opened only if this full-protocol pass recovers genuinely new qualifying primary evidence for the blocking dimension. Repetition of the same previously reviewed official statement does not close a case.

## Acceptance
`SRC-2022-RU_OFFICIAL` may become PASS only after:
- every month×family cell is COMPLETED;
- CoverageStatus=FULL_PROTOCOL;
- dependency audit is complete;
- every retained raw/source component is transferred to the candidate ledger or documented as a non-candidate;
- ReviewStatus=COMPLETE;
- DedupeReviewStatus=COMPLETE;
- source-component-to-ledger reconciliation balances exactly;
- evidence/archive paths are versioned and committed.

C2/C6 implications are evaluated only after the lane itself reaches PASS.
CandidateCensusComplete remains FALSE unless the global DEEP-COMP-V1 rule is satisfied.
