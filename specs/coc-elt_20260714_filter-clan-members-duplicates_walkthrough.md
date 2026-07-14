---
title: "Filter Duplicate Clan Members and Retrieve Latest Daily Update Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "2446725b-e34d-4274-b7da-dc565c7b5691"
artifact_type: "Data Engineering Pattern"
tags:
  - "dataform"
  - "deduplication"
  - "walkthrough"
source_uri: "specs/coc-elt_20260714_filter-clan-members-duplicates_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-14T06:00:17-05:00
- **Objective**: Implement the approved plan to filter duplicate clan member records on each day, ensuring the latest update of the day is retrieved for each player.

### Executed Commands
- `pnpm exec dataform compile`

### State Mutations
- **Created**:
  - `specs/coc-elt_20260714_filter-clan-members-duplicates_walkthrough.md`
- **Modified**:
  - `definitions/clan_members.sqlx`
  - `specs/coc-elt_20260714_filter-clan-members-duplicates_implementation_plan.md`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: The model handles the ingestion and formatting of members data from the bronze layer, separating extraction (`parsed_members` CTE) and ranking (`ranked_members` CTE) to keep queries legible.
- **ROW_NUMBER OVER Partitioning**: Leveraging `ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC)` ensures that only the most recent state for each player on a given date is kept.
- **Incremental Lookback & Partition Pruning**: Maintained the lookback window `extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))` for incremental runs.
- **Data Integrity**: Enforced unique key assertions on `(extracted_date, ptag)` to guarantee downstream tables don't consume duplicate daily records.

### Validation Artifacts
- The compilation step completed successfully:
```text
Compiled 3 action(s).
1 dataset(s):
  coc_silver.clan_members [incremental]
2 assertion(s):
  coc_assertions.coc_silver_clan_members_assertions_uniqueKey_0
  coc_assertions.coc_silver_clan_members_assertions_rowConditions
```

### Technical Debt
- None.
