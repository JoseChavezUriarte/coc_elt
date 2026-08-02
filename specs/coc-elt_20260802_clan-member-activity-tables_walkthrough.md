---
title: "Dual-Asset Clan Member Activity Architecture Walkthrough"
project_id: "coc-elt"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "bigquery"
  - "gold-layer"
  - "walkthrough"
source_uri: "specs/coc-elt_20260802_clan-member-activity-tables_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-08-02T14:58:27-05:00
- **Objective**: Execute the approved plan to create `clan_member_activity_historical.sqlx` and `clan_member_activity_hot.sqlx` in dataset `coc_gold`, establishing a decoupled dual-asset architecture for tracking daily member activity scores.

### Executed Commands
- `pnpm dataform compile`

### State Mutations
- **Created**:
  - `definitions/clan_member_activity_historical.sqlx` (Incremental asset in dataset `coc_gold`)
  - `definitions/clan_member_activity_hot.sqlx` (Hot serving table in dataset `coc_gold`)
  - `specs/coc-elt_20260802_clan-member-activity-tables_walkthrough.md`

### Architectural Decisions (ADR) and SOLID
- **Decoupled Dual-Asset Model**: Separates historical partitioned snapshotting (`clan_member_activity_historical`) from fast single-partition access (`clan_member_activity_hot`).
- **Strict Dataset Scoping**: Explicitly specified `schema: "coc_gold"` in both definitions.
- **Deterministic Temporal Filtering & Unconditional Bounded Window**: Replaced nondeterministic runtime functions (`CURRENT_DATE()`, `CURRENT_TIMESTAMP()`) with deterministic timestamp parameters (`execution_ts = dataform.projectConfig.vars.execution_timestamp || "2026-08-02T12:00:00Z"`). Removed `${when(incremental(), ...)}` macro wrapper across all 5 `SELECT` statements in `unified_metrics` in favor of an unconditional 7-day temporal window clause (`WHERE extracted_date BETWEEN DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY) AND DATE('${execution_ts}')`), ensuring identical 7-day snapshot behavior during both incremental and `--full-refresh` runs.
- **Literal Partition Pruning (FinOps Optimization)**: Uses exact literal timestamp comparison `WHERE generated_at = TIMESTAMP('${execution_ts}')` in `clan_member_activity_hot.sqlx` to ensure constant-time partition pruning without scanning unnecessary data in BigQuery.
- **7-Dimension Activity Aggregation**: Aggregates binary indicators for wars, capital contributions, town hall upgrades, hero upgrades, spell upgrades, troop upgrades, and hero equipment upgrades (activity score 0 to 7).

### Validation Artifacts
- The `pnpm dataform compile` execution succeeded cleanly with 0 errors:
```text
Compiled 48 action(s).
16 dataset(s):
  coc_silver.clan_description [incremental]
  coc_gold.clan_member_activity_historical [incremental]
  coc_gold.clan_member_activity_hot [table]
  coc_silver.clan_member_upgrades [incremental]
  coc_silver.clan_members [incremental]
  coc_gold.clan_weekly_performance [incremental]
  coc_silver.coc_member_achievements [incremental]
  coc_silver.coc_member_hero_upgrades [incremental]
  coc_silver.coc_member_hero [incremental]
  coc_silver.coc_member_heroEquips_upgrades [incremental]
  coc_silver.coc_member_heroEquips [incremental]
  coc_silver.coc_member_spells_upgrades [incremental]
  coc_silver.coc_member_spells [incremental]
  coc_silver.coc_member_troops_upgrades [incremental]
  coc_silver.coc_member_troops [incremental]
  coc_silver.wars [incremental]
32 assertion(s):
  coc_assertions.coc_gold_clan_member_activity_historical_assertions_uniqueKey_0
  coc_assertions.coc_gold_clan_member_activity_historical_assertions_rowConditions
  coc_assertions.coc_gold_clan_member_activity_hot_assertions_uniqueKey_0
  coc_assertions.coc_gold_clan_member_activity_hot_assertions_rowConditions
```

### Technical Debt
- None.
