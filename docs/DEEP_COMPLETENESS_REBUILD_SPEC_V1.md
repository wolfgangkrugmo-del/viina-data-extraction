# DEEP Completeness Rebuild 2022–2026 — Specification V1

## 1. Scope

Study window: **2022-02-24 through 2026-06-30**, inclusive. The rebuild concerns discovery and census completeness for Ukrainian deep-strike candidates against **Russia proper**. Crimea/Sevastopol and other internationally recognized Ukrainian territory are retained in the discovery audit but are outside the Russia-proper census.

`CandidateCensusComplete` is **FALSE by default** and may become TRUE only on the single `GLOBAL_SUMMARY` row after C1–C7 are all TRUE. No source row or individual candidate may independently make the census complete.

## 2. Row types

- `SOURCE`: one year × one discovery lane. Records access, executed search protocol, coverage, yield, review and dedupe status.
- `YEAR_SUMMARY`: one row per year. Carries the annual C1–C7 gate decisions.
- `GLOBAL_SUMMARY`: one row for the full study window. This is the only row allowed to set `CandidateCensusComplete=TRUE`.

## 3. Frozen source lanes

| SourceID | Role | Dependence group | C1 core? |
|---|---|---|---|
| `VIINA` | CORE_DISCOVERY | `DG_VIINA` | TRUE |
| `REUTERS` | CORE_DISCOVERY | `DG_REUTERS` | TRUE |
| `BAKER` | VALIDATION | `DG_BAKER` | FALSE |
| `ACLED` | VALIDATION | `DG_ACLED` | FALSE |
| `UA_OFFICIAL` | SUPPLEMENTAL_DISCOVERY | `DG_UA_OFFICIAL` | FALSE |
| `RU_OFFICIAL` | SUPPLEMENTAL_DISCOVERY | `DG_RU_OFFICIAL` | FALSE |
| `OSINT_SECTOR` | VALIDATION_DISCOVERY | `DG_OSINT_SPECIALIST` | FALSE |

A nominally different source does **not** create a new independence group if it is demonstrably derivative of another lane. `DependencyAuditStatus` must be completed before a lane counts toward C2 or C6.

## 4. Allowed matrix status values

### AccessStatus
`AVAILABLE`, `PARTIAL`, `ACCESS_REQUIRED`, `REQUEST_PENDING`, `FORMALLY_UNAVAILABLE`, `NA`.

### SearchStatus
`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED`, `NOT_APPLICABLE`.

### CoverageStatus
`UNKNOWN`, `PARTIAL`, `FULL_PROTOCOL`, `NO_ARCHIVE`, `NOT_APPLICABLE`.

### DependencyAuditStatus
`NOT_REVIEWED`, `INDEPENDENT`, `PARTLY_DERIVATIVE`, `DERIVATIVE`, `NA`.

### ReviewStatus / DedupeReviewStatus
`NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`, `BLOCKED`.

### StopRuleStatus
`NOT_EVALUATED`, `NOT_MET`, `MET`, `FAILED`.

### Gate fields C1–C7
`TRUE`, `FALSE`, `UNCERTAIN`, `NA`. `NA` is allowed only on SOURCE rows where the gate is evaluated at YEAR/GLOBAL level.

### RowAcceptanceStatus
`NOT_READY`, `PASS`, `PASS_WITH_DOCUMENTED_UNAVAILABILITY`, `FAIL`.

### YearAcceptanceStatus
`NOT_READY`, `PASS`, `FAIL`, `NA`.

## 5. Candidate-ledger mandatory fields

Every discovered candidate, including exclusions and duplicates, must be preserved in the candidate ledger with at least:

`CandidateRecordID`, `DiscoveryYear`, `SourceID`, `SourceDependenceGroup`, `SourceRecordID`, `SourceURL`, `SourcePublishedAt`, `FirstPublicSignalAt`, `EventStart`, `EventEnd`, `CanonicalEventDate`, `ActorClaim`, `AttackMethod`, `LocationText`, `CountryScope`, `Region`, `Latitude`, `Longitude`, `TargetName`, `TargetID`, `NodeID`, `ProvisionalTargetGroupID`, `TargetClass`, `Sector`, `CriticalityStatus`, `PhysicalAttackStatus`, `OperationalDisruptionStatus`, `DisruptionStart`, `DisruptionDurationHours`, `IndependentConfirmationStatus`, `ConfirmationSourceID`, `InclusionStatus`, `ExclusionReason`, `SplitStatus`, `ParentCandidateRecordID`, `RelatedEventID`, `DedupeKeyDate`, `DedupeKeyLocation`, `DedupeKeyTarget`, `DedupeKeyNode`, `DedupeClusterID`, `DedupeDecision`, `CanonicalCandidateRecordID`, `ConflictStatus`, `OutcomeRelevantUnresolved`, `ReviewStatus`, `ReviewedAt`, `Reviewer`, `EvidenceQuoteOrNote`, `EvidenceArchivePath`, `CandidateCensusComplete`.

## 6. Candidate-level controlled values

### CountryScope
`RUSSIA_PROPER`, `CRIMEA_SEVASTOPOL`, `UKRAINE_OCCUPIED_OTHER`, `OTHER`, `UNKNOWN`.

### PhysicalAttackStatus
`CONFIRMED`, `CLAIMED`, `UNCERTAIN`, `NOT_EVENT`.

### CriticalityStatus
`TRUE`, `FALSE`, `UNCERTAIN`, `NOT_ASSESSED`.

### OperationalDisruptionStatus
`CONFIRMED_GT72H`, `CONFIRMED_GT24H`, `CONFIRMED_LE24H`, `CONFIRMED_NO_OUTAGE`, `UNCERTAIN`, `NOT_ASSESSED`.

### IndependentConfirmationStatus
`CONFIRMED_INDEPENDENT`, `SINGLE_SOURCE`, `DEPENDENT_CONFIRMATION`, `CONTRADICTED`, `UNRESOLVED`.

### InclusionStatus
`INCLUDE_RUSSIA_PROPER`, `EXCLUDE_OUTSIDE_RUSSIA_PROPER`, `EXCLUDE_CRIMEA_SCOPE`, `EXCLUDE_NOT_EVENT`, `EXCLUDE_OTHER_SCOPE`, `DUPLICATE`, `UNRESOLVED`.

### SplitStatus
`NOT_APPLICABLE`, `SPLIT_REQUIRED`, `SPLIT_COMPONENT_RESOLVED`, `SPLIT_COMPONENT_TARGET_ID_UNRESOLVED`, `FUNCTIONAL_COMPLEX_NOT_SPLIT`, `FUNCTIONAL_NODE_AGGREGATED`.

### DedupeDecision
`UNIQUE`, `CANONICAL`, `DUPLICATE_LINKED`, `NOT_ASSESSABLE_UNRESOLVED_TARGET`.

### ConflictStatus
`NONE`, `SOURCE_DATE_CONFLICT`, `LOCATION_CONFLICT`, `TARGET_CONFLICT`, `ACTOR_CONFLICT`, `MULTIPLE`.

`OutcomeRelevantUnresolved` is strictly `TRUE` or `FALSE`.

## 7. Dedupe rules

1. **Split before dedupe.** A composite article is first decomposed into physical target/node components. The parent report is never counted as an additional event.
2. **Canonical event time beats publication time.** `CanonicalEventDate` is based on the attack event, not the reporting date.
3. **Same physical node, same attack wave:** reports referring to the same `NodeID` within one 24-hour attack wave are one canonical event unless sources explicitly establish separate attacks.
4. **Same target with NodeID unavailable:** duplicate only when date/time, location and narrative evidence jointly establish the same physical attack. Name similarity alone is insufficient.
5. **Repeat attacks remain distinct.** A later new attack on the same `NodeID` is a separate event; it may feed repeat-attack rules.
6. **Follow-ups are linked, not counted.** Fire duration, repair status, political reaction, satellite aftermath or production effects without a fresh attack are linked through `RelatedEventID`.
7. **Exact duplicate source records:** same source URL/text replicated on adjacent VIINA days are `DUPLICATE_LINKED` to one canonical record.
8. **Unresolved identity:** if a unique physical facility cannot be identified, leave `TargetID` and `NodeID` blank and use `ProvisionalTargetGroupID`. Such a record cannot be declared `UNIQUE` at target/node level.
9. **DedupeClusterID** must be populated for every multi-record cluster; one record is `CANONICAL`, all others `DUPLICATE_LINKED`.
10. A source-lane dedupe review is `COMPLETE` only when no duplicate cluster remains without a canonical record.

## 8. Source-row acceptance

A SOURCE row is `PASS` only if:

- `SearchStatus=COMPLETED`;
- `CoverageStatus=FULL_PROTOCOL` for its stated year window;
- `DependencyAuditStatus` is not `NOT_REVIEWED`;
- all discovered raw hits have been transferred to the candidate ledger or documented as machine-level non-candidates under the frozen query protocol;
- `ReviewStatus=COMPLETE` and `DedupeReviewStatus=COMPLETE` for all candidate rows generated by that lane;
- evidence/query logs are archived in `EvidenceArchivePath`.

A source that cannot legally or technically be accessed may be `PASS_WITH_DOCUMENTED_UNAVAILABILITY` only when `AccessStatus=FORMALLY_UNAVAILABLE` and the reason/evidence is recorded. Such a lane does **not** count toward C2 or C6.

## 9. Annual and global acceptance gates C1–C7

### C1 — Time coverage
**YEAR TRUE iff** both frozen core lanes (`VIINA`, `REUTERS`) have `CoverageStatus=FULL_PROTOCOL` over every day of that year's study window, or a core lane has a formally documented permanent unavailability approved before the search and is replaced by a designated independent lane with full coverage. There may be **no uncovered calendar day** in the accepted core coverage. For 2022 the window begins 24 February; for 2026 it ends 30 June.

**GLOBAL TRUE iff** C1 is TRUE for all five YEAR_SUMMARY rows.

### C2 — Independent discovery
**YEAR TRUE iff** at least **two full-protocol lanes in distinct, dependency-audited groups** cover the full year window, and at least one is a core lane. `PARTLY_DERIVATIVE` lanes may not be paired as the sole two independent lanes if they share the same upstream event list.

**GLOBAL TRUE iff** C2 is TRUE for all five years and at least three distinct dependence groups contributed to the merged full-period candidate ledger.

### C3 — All candidates coded
**YEAR TRUE iff** every discovered candidate has a nonblank `InclusionStatus` and every exclusion has a controlled `ExclusionReason`; no candidate remains merely absent from the ledger. `UNRESOLVED` is a valid code but will be tested by C5.

**GLOBAL TRUE iff** C3 is TRUE for all years and the raw-hit-to-ledger reconciliation count balances for every accepted source lane.

### C4 — Dedupe complete
**YEAR TRUE iff** every candidate has a completed dedupe decision, every duplicate cluster has exactly one canonical record, all duplicates link through `CanonicalCandidateRecordID`, and there is **no** `NOT_ASSESSABLE_UNRESOLVED_TARGET` record capable of being the same event as another included candidate.

**GLOBAL TRUE iff** C4 is TRUE in each year **and** a cross-year boundary dedupe check (31 Dec/1 Jan ±48 h) finds no unresolved duplicate cluster.

### C5 — No outcome-relevant unresolved cases
**YEAR TRUE iff** there is **zero** record with `OutcomeRelevantUnresolved=TRUE`. This includes unresolved event identity, Russia-proper geography, `TargetID`/`NodeID`, criticality, sector, or event separation whenever the uncertainty could change OA/ROT-A target counts, sector counts, repeat-node logic or the realized outcome classification.

**GLOBAL TRUE iff** C5 is TRUE for all five years.

### C6 — Source convergence / saturation
**YEAR TRUE iff all conditions hold:**

1. at least **four** full-protocol discovery/validation lanes from distinct dependency groups have been merged for that year;
2. the final **two** independent validation/supplemental passes each add **no more than one** new valid Russia-proper event;
3. their combined marginal yield is **≤2.0%** of the unique Russia-proper register size immediately before those two passes;
4. neither pass discovers a new event that changes an already stable OA/ROT-A window classification;
5. if any later lane adds >1 event, >2.0% marginal yield, or changes a window classification, C6 resets to FALSE and another independent validation pass is required.

For small yearly registers where one new event exceeds 2.0%, the practical consequence is that the final two validation passes must add **zero** new events.

**GLOBAL TRUE iff** C6 is TRUE for every year and a final full-period gap search adds zero outcome-relevant unique events.

### C7 — Versioned freeze
**YEAR TRUE iff** C1–C6 are TRUE and the following are committed: accepted source-row matrix, candidate ledger, dedupe/correction log, query protocol version, evidence/archive references and a manifest containing row counts plus hashes/version identifiers.

**GLOBAL TRUE iff** all YEAR rows have C7 TRUE, the merged register has a frozen version identifier and commit SHA, the global manifest records the study window and source-lane versions, and there are no open correction items that could alter event/target/node counts. Any post-freeze substantive correction requires a new census version and resets C7 until revalidated.

## 10. CandidateCensusComplete rule

`CandidateCensusComplete=TRUE` is permitted **only** on `GLOBAL_SUMMARY` when:

`C1 AND C2 AND C3 AND C4 AND C5 AND C6 AND C7 = TRUE`

and every YEAR_SUMMARY has `YearAcceptanceStatus=PASS`.

Until then, all source, year and candidate records retain `CandidateCensusComplete=FALSE`.

## 11. Execution order

Run the rebuild year by year: **2022 → 2023 → 2024 → 2025 → 2026**. Within each year execute the core lanes first, reconcile candidates and dedupe, then add validation/supplemental lanes until C6 is met. Do not calculate count-based FALSE outcomes for DEEP OA/ROT-A from a year whose C1–C7 acceptance is incomplete.
