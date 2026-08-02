---
title: "Create coc_member Upgrade Tracking Models in coc_silver Walkthrough"
project_id: "coc-elt"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "silver-layer"
  - "walkthrough"
source_uri: "specs/coc-elt_20260802_create-coc-member-upgrades-tables_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-08-02T11:04:29-05:00
- **Objective**: Detailed walkthrough specification for creating three denormalized incremental Dataform tables (`coc_silver.coc_member_troops_upgrades`, `coc_silver.coc_member_heroEquips_upgrades`, `coc_silver.coc_member_spells_upgrades`) tracking daily level upgrades achieved by clan members across troops, hero equipment, and spells.

---

### Executed & Planned Commands

1. **Compilation Verification**:
   ```bash
   pnpm dataform compile
   ```
   *Executed in `/home/scheveningen/documents/proyectos/coc_elt` to verify Dataform AST compilation, dependency graph, and assertions.*

2. **Nyutu Memory Cornerstone Recording**:
   ```bash
   uv run --project /home/scheveningen/.gemini/config/plugins/cerelino/skills/nyutu-mng/commands \
     /home/scheveningen/.gemini/config/plugins/cerelino/skills/nyutu-mng/commands/save_cornerstone.py \
     --title "Create Member Troops, HeroEquips, and Spells Upgrades Tables in coc_silver" \
     --artifact-type "Infrastructure Pattern" \
     --content "Pattern implementation of coc_member_troops_upgrades, coc_member_heroEquips_upgrades, and coc_member_spells_upgrades incremental tables using target anchoring (${self()}), 7-day lookback window, LAG() windowing, and idempotent insertion." \
     --project-id "coc-elt" \
     --source-uri "specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md"
   ```

---

### State Mutations

- **Created / Target Artifacts**:
  - [`definitions/coc_member_troops_upgrades.sqlx`](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_troops_upgrades.sqlx)
  - [`definitions/coc_member_heroEquips_upgrades.sqlx`](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_heroEquips_upgrades.sqlx)
  - [`definitions/coc_member_spells_upgrades.sqlx`](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_spells_upgrades.sqlx)
  - [`specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md)
  - [`specs/coc-elt_20260802_create-coc-member-upgrades-tables_walkthrough.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260802_create-coc-member-upgrades-tables_walkthrough.md)

---

### Architectural Decisions (ADR) & Logic Flow

#### 1. Table Specifications & Dataform Configurations

All three new models are configured as incremental datasets in schema `coc_silver`, partitioned daily on `extracted_date` and clustered on `["ptag", "<entity_key>"]`:

1. **`coc_member_troops_upgrades`**:
   - Source table: `${ref("coc_member_troops")}`
   - Entity key: `troop_name`
   - Source level attribute: `troop_level`
   - Unique key: `["extracted_date", "ptag", "troop_name"]`
   - Assertions: `uniqueKey` on `["extracted_date", "ptag", "troop_name"]`, `nonNull` on `["extracted_date", "ptag", "troop_name", "current_level", "prev_level"]`.

2. **`coc_member_heroEquips_upgrades`**:
   - Source table: `${ref("coc_member_heroEquips")}`
   - Entity key: `equipment_name`
   - Source level attribute: `equipment_level`
   - Unique key: `["extracted_date", "ptag", "equipment_name"]`
   - Assertions: `uniqueKey` on `["extracted_date", "ptag", "equipment_name"]`, `nonNull` on `["extracted_date", "ptag", "equipment_name", "current_level", "prev_level"]`.

3. **`coc_member_spells_upgrades`**:
   - Source table: `${ref("coc_member_spells")}`
   - Entity key: `spell_name`
   - Source level attribute: `spell_level`
   - Unique key: `["extracted_date", "ptag", "spell_name"]`
   - Assertions: `uniqueKey` on `["extracted_date", "ptag", "spell_name"]`, `nonNull` on `["extracted_date", "ptag", "spell_name", "current_level", "prev_level"]`.

#### 2. Target Anchoring via `${self()}` & Incremental Lookback Window

- **Incremental Mode (`when(incremental())`)**:
  - **State Anchoring**: `target_anchor` CTE calculates `max_target_date` using `COALESCE(MAX(extracted_date), DATE('1970-01-01')) FROM ${self()}`. If the target table is empty, it evaluates to `1970-01-01`.
  - **Lookback Window**: Source table is filtered to `extracted_date >= DATE_SUB(max_target_date, INTERVAL 7 DAY)`. This limits query scan cost while supplying required preceding rows for `LAG()` across partition boundaries.
  - **Idempotent Single-Append**: The outer query applies `WHERE level_var > 0 AND extracted_date > max_target_date`.
- **Full Refresh Mode (`when(!incremental())`)**:
  - Scans full history of the source silver table without date sub filters.
  - Computes `LAG()` window function over `(PARTITION BY ptag, <entity_key> ORDER BY extracted_date ASC)`.
  - Filters for records where `level_var > 0`.

#### 3. Action Count Transformation

- **Baseline Environment**: 30 total Dataform actions (10 dataset models, 20 assertions).
- **Post-Implementation Projection**: 39 total Dataform actions (13 dataset models, 26 assertions).
- Each new dataset adds:
  - 1 incremental table action (`coc_silver.coc_member_<entity>_upgrades`)
  - 1 uniqueKey assertion action (`coc_assertions.coc_silver_coc_member_<entity>_upgrades_assertions_uniqueKey_0`)
  - 1 nonNull assertion action (`coc_assertions.coc_silver_coc_member_<entity>_upgrades_assertions_rowConditions`)

---

### Verification Results Matrix

| Metric / Check | Target Value | Verification Method |
|----------------|--------------|--------------------|
| Dataform Compilation | Clean (0 errors) | `pnpm dataform compile` |
| Total Dataform Actions | 39 actions (13 datasets, 26 assertions) | AST Action inventory inspection |
| Nyutu Memory Recording | Status 200 / Saved | `save_cornerstone.py` execution |
