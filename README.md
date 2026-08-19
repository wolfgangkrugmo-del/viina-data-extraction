# VIINA Deep-Strike Candidate Extraction

Public helper repository for extracting a high-recall candidate set from the public VIINA 2.0 event dataset for the DEEP-STRIKE/MIC historical backtest.

Study period: 2022-02-24 through 2026-06-30.

The workflow clones VIINA with Git LFS, pulls the 2022–2026 `event_info` and `event_1pd` archives, restricts events to GeoNames locations in the Russian Federation, screens raw report text for relevant target and attack terms, joins the retained reports to VIINA's one-per-day events, and writes `output/viina_deep_strike_candidates.csv`.

The output is a discovery dataset only. Criticality, TargetID/NodeID, sector, D24/D72 and source-independence remain subject to the frozen backtest rules.

## License
Contains information from VIINA 2.0 (Yuri Zhukov and Natalie Ayers), made available under ODbL v1.0. The derived candidate database is distributed under the same ODbL terms.
