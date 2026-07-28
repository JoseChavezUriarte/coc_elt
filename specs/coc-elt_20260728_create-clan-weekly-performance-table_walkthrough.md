---
title: "Create clan_weekly_performance Table in coc_gold Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "f2a219be-ca01-46dc-8c11-57d4ac14acf7"
artifact_type: "Walkthrough"
tags:
  - "dataform"
  - "bigquery"
  - "gold-layer"
  - "walkthrough"
source_uri: "specs/coc-elt_20260728_create-clan-weekly-performance-table_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-28T14:53:00-05:00
- **Objective**: Create the `coc_gold.clan_weekly_performance` incremental table in Dataform to track weekly performance cohorts of the clan based on daily snapshots.

### Executed Commands
- `pnpm exec dataform compile` (verified that the Dataform compilation pipeline succeeds with 0 errors)

### State Mutations
- **Created**:
  - `definitions/clan_weekly_performance.sqlx` (defines the SQLX incremental table)
  - `specs/coc-elt_20260728_create-clan-weekly-performance-table_walkthrough.md` (this walkthrough document)
- **Modified**:
  - `specs/coc-elt_20260728_create-clan-weekly-performance-table_implementation_plan.md` (updated checklist to mark tasks completed and aligned query structure)

### Architectural Decisions (ADR) and SOLID
- **Weekly Cohort Alignment**: Aggregated data starts on Monday (`WEEK(MONDAY)`) for standard business alignment.
- **Idempotent Upsert Logic**: Configured `week_start_date` as the `uniqueKey` to allow daily runs to update the current week's record incrementally, only adding a new record when a new week begins.
- **No Partitioning / Clustering**: Omitted storage structures due to low data volume, adhering to the YAGNI principle.
- **Dependency Management**: Referenced input data via `${ref("clan_description")}` to establish explicit dependency and execution ordering.

### Validation Artifacts
- **Dataform Compilation**: Successful project compilation (0 errors) confirming syntax and dependency validation.
