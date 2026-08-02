---
title: "Create clan_member_upgrades Table in coc_silver Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "10d99b13-9de4-491e-a975-a91b9ae32412"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "incremental-load"
  - "silver-layer"
  - "walkthrough"
source_uri: "specs/coc-elt_20260802_clan_member_upgrades_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-08-02T12:31:18-05:00
- **Objective**: Implement the Dataform SQLX model `coc_silver.clan_member_upgrades` tracking player member daily stat progressions (`war_stars_var`, `capital_contrib_var`, `thl_var`) derived from `clan_members`, verify 0 compilation errors across 42 actions, and save the Nyutu architectural decision cornerstone.

### Executed Commands & Verifications
- `pnpm dataform compile` (Executed in `/home/scheveningen/documents/proyectos/coc_elt` to verify Dataform SQLX compilation across 42 actions).
- `uv run ... save_cornerstone.py` (Executed to record the architectural decision cornerstone in Nyutu long-term architectural memory).

### Created Files & State Mutations
- **Created**:
  - `specs/coc-elt_20260802_clan_member_upgrades_implementation_plan.md`
  - `specs/coc-elt_20260802_clan_member_upgrades_walkthrough.md`
  - `definitions/clan_member_upgrades.sqlx`

---

### Architectural Walkthrough & Design Rationale

#### 1. Dataform Config & Table Specification
The table `coc_silver.clan_member_upgrades` materializes incrementally in BigQuery:
- **Target Schema & Table**: `coc_silver.clan_member_upgrades`
- **Partitioning**: Partitioned by `extracted_date` (DAY) for optimal query scan cost.
- **Clustering**: Clustered on `["ptag", "war_stars_var", "capital_contrib_var", "thl_var"]` to enable fast filtering on player tag and metric variances.
- **Unique Key**: `["extracted_date", "ptag"]` ensures each player has at most one progression record per extraction date.
- **Assertions**:
  - `uniqueKey: ["extracted_date", "ptag"]` guarantees entity uniqueness.
  - `nonNull: ["extracted_date", "ptag", "war_stars_var", "capital_contrib_var", "thl_var"]` ensures mandatory fields are populated.
- **Metadata**: Labeled with `environment: "production"`, `domain: "clash-of-clans"`, `layer: "silver"`.

#### 2. Target Anchoring via `${self()}` & 7-Day Lookback Window Explanation
- **State Anchoring (`target_anchor` CTE)**:
  `SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date FROM ${self()}`
  This queries the current target table to establish the high-water mark date (`max_target_date`) dynamically during incremental execution.

- **Lookback Window (`member_history` CTE)**:
  `WHERE extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)`
  Because `LAG()` window functions require preceding historical rows to compute differences (`war_stars - LAG(war_stars, 1)`), evaluating only un-ingested dates would yield `NULL` for `prev_*` values. Including a 7-day lookback window ensures `LAG()` receives sufficient context across partition boundaries while minimizing BigQuery scanning cost.

#### 3. Idempotent Insertion Logic
- **Incremental Mode Filter**:
  `WHERE (war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0) AND extracted_date > (SELECT max_target_date FROM target_anchor)`
  The `extracted_date > max_target_date` predicate prevents re-inserting already processed dates. Combined with the positive variance check `(war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0)`, only meaningful stat gains are appended to `coc_silver.clan_member_upgrades`.

- **Full Refresh Mode Filter**:
  `WHERE (war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0)`
  During full table rebuilds (`--full-refresh`), the lookback window and `max_target_date` filter are bypassed, processing all available historical snapshots while preserving positive variance filtering.

---

### Dataform Compilation Verification

```bash
cd /home/scheveningen/documents/proyectos/coc_elt
pnpm dataform compile
```

**Expected Compilation Output**:
- Exit Code: 0
- Total Actions: 42 (14 Datasets, 28 Assertions)
- Newly Compiled Dataset: `coc_silver.clan_member_upgrades [incremental]`
- Newly Compiled Assertions:
  - `coc_assertions.coc_silver_clan_member_upgrades_assertions_uniqueKey_0`
  - `coc_assertions.coc_silver_clan_member_upgrades_assertions_rowConditions`

---

### Nyutu Memory Cornerstone Details

- **Title**: `Silver Upgrade Model: clan_member_upgrades Dataform SQLX Model`
- **Artifact Type**: `Architectural Decision`
- **Project ID**: `coc-elt`
- **Source URI**: `definitions/clan_member_upgrades.sqlx`
- **Content Summary**: Implemented `coc_silver.clan_member_upgrades` incremental Dataform SQLX model tracking daily player member stat progressions (`war_stars_var`, `capital_contrib_var`, `thl_var`) from `clan_members`. Applied target anchoring via `${self()}`, 7-day lookback window, idempotent insertion filter, partitioning on `extracted_date`, clustering, `uniqueKey` and `nonNull` assertions, and comprehensive column documentation.
