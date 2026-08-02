---
title: "Create coc_member_hero_upgrades Table in coc_silver Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "b133af9e-9a42-4bcd-a97a-e59447e3adc6"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "silver-layer"
  - "walkthrough"
source_uri: "specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-08-02T10:50:36-05:00
- **Objective**: Implement the approved plan to create a denormalized incremental Dataform table `coc_silver.coc_member_hero_upgrades` tracking daily hero level upgrades achieved by clan members.

### Executed Commands
- `pnpm dataform compile` (in `/home/scheveningen/documents/proyectos/coc_elt` to verify SQLX compilation)

### State Mutations
- **Created**:
  - [`definitions/coc_member_hero_upgrades.sqlx`](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_hero_upgrades.sqlx)
  - [`specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_walkthrough.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_walkthrough.md)

### Architectural Decisions (ADR) and Logic Flow

#### 1. Table Specification & Dataform Config
The model `coc_silver.coc_member_hero_upgrades` is configured as an incremental dataset partitioned daily on `extracted_date` and clustered on `["ptag", "hero_name"]`:
- **Unique Key**: `["extracted_date", "ptag", "hero_name"]`
- **Assertions**:
  - `uniqueKey`: `["extracted_date", "ptag", "hero_name"]`
  - `nonNull`: `["extracted_date", "ptag", "hero_name", "current_level", "prev_level"]`
- **Metadata**: Labels for `environment: "production"`, `domain: "clash-of-clans"`, `layer: "silver"`.

#### 2. Target Anchoring via `${self()}` & Incremental Lookback Window
- **Incremental Mode (`when(incremental())`)**:
  - Anchors target maximum date: `target_anchor` CTE reads `COALESCE(MAX(extracted_date), DATE('1970-01-01')) FROM ${self()}`.
  - Source window filter: restricts `${ref("coc_member_hero")}` to `extracted_date >= DATE_SUB(max_target_date, INTERVAL 7 DAY)` to provide necessary historical context for `LAG()` across partition boundaries.
  - Append condition: filters final output to `extracted_date > max_target_date` and `level_var > 0` for idempotent insertions.
- **Full Refresh Mode (`when(!incremental())`)**:
  - Evaluates full `hero_history` over window `w_equip AS (PARTITION BY ptag, hero_name ORDER BY extracted_date ASC)`.
  - Filters for records where `level_var > 0`.

#### 3. Dataform Compilation Verification
Executed `pnpm dataform compile` in `/home/scheveningen/documents/proyectos/coc_elt`. Result:
- Compiled 30 actions cleanly (10 datasets, 20 assertions) with 0 errors.
- Included `coc_silver.coc_member_hero_upgrades [incremental]` and its corresponding assertions `coc_assertions.coc_silver_coc_member_hero_upgrades_assertions_uniqueKey_0` and `coc_assertions.coc_silver_coc_member_hero_upgrades_assertions_rowConditions`.
