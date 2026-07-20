---
title: "Denormalized Incremental Silver Tables for Member Details Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "4a1809b3-9746-4ee5-bff8-e18adb8d195b"
artifact_type: "Data Engineering Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "unnesting"
  - "deduplication"
  - "walkthrough"
source_uri: "specs/coc-elt_20260720_denormalized-silver-tables_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-20T18:29:12-05:00
- **Objective**: Implement the approved plan to create 5 new denormalized, incremental Dataform tables in the `coc_silver` schema to process raw array payloads from `coc_bronze.coc_members`.

### Executed Commands
- `pnpm exec dataform compile` (in the repository root to verify SQLX compilation)

### State Mutations
- **Created**:
  - `definitions/coc_member_achievements.sqlx`
  - `definitions/coc_member_heroEquips.sqlx`
  - `definitions/coc_member_hero.sqlx`
  - `definitions/coc_member_spells.sqlx`
  - `definitions/coc_member_troops.sqlx`
  - `specs/coc-elt_20260720_denormalized-silver-tables_walkthrough.md`
- **Modified**:
  - `specs/coc-elt_20260720_denormalized-silver-tables_revised_implementation_plan.md`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Each new SQLX model is dedicated to a single array field in the member record (achievements, heroEquipment, heroes, spells, and troops), decoupling downstream analytics from raw JSON arrays.
- **Two-Stage Deduplication**:
  1. *Player Day Level Deduplication*: Staged in the `ranked_members` and `deduped_members` CTEs. Deduplicates incoming rows by partitioning on `extracted_date` and `ptag` and keeping the latest record (`ROW_NUMBER() ... ORDER BY extracted_at DESC = 1`). This avoids unnecessary unnesting of redundant payloads.
  2. *Array Element Level Deduplication*: After unnesting arrays in the final query block, a `QUALIFY` clause is applied: `ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, [item_name] ORDER BY [item_level_or_value] DESC) = 1`. This handles raw payload anomalies where duplicate items might exist within the same array payload, keeping the highest level/value.
- **FinOps and Partitioning**: Enforces partition pruning. Each table is partitioned by `extracted_date` and clustered on commonly filtered keys (e.g. `ptag`, item name, item level/value, etc.). During incremental runs, only the last 2 days of data are updated using the compilation override `updatePartitionFilter` and dynamic `incremental()` check.
- **Dependency Inversion / Declarative References**: Tables dynamically refer to the bronze table via `${ref("coc_members")}` rather than hardcoding dataset names.

### Validation Assertions
Dataform compiles and generates verification assertions for each model:
1. **Unique Key Constraint**: Ensures that the combined unique key of the table (`extracted_date`, `ptag`, and item name) is unique across all rows.
2. **Non-Null Constraint**: Asserts that `extracted_date`, `ptag`, and item name are not null, preventing malformed data from polluting the silver layer.

### Technical Debt
- None identified.
