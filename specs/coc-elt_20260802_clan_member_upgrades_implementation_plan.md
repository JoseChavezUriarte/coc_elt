---
title: "Create clan_member_upgrades Table in coc_silver"
project_id: "coc-elt"
nyutu_uuid: "10d99b13-9de4-491e-a975-a91b9ae32412"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260802_clan_member_upgrades_implementation_plan.md"
---

## 1. User Request Summary
The requirement is to create a new Dataform SQLX incremental model named `clan_member_upgrades` (`definitions/clan_member_upgrades.sqlx`) in the `coc_silver` schema. This model tracks player member daily stat progressions (`war_stars_var`, `capital_contrib_var`, `thl_var`) derived from `${ref("clan_members")}`, strictly following the established 4-tier silver upgrade architectural pattern in `coc_elt`.

## 2. Architectural Requirements (R1 - R3)

### R1. Dataform Model Specifications
- **Target Schema & Table**: `coc_silver.clan_member_upgrades`
- **Materialization Type**: `type: "incremental"`
- **Source Dataset**: `${ref("clan_members")}`
- **Partitioning**: `partitionBy: "extracted_date"` (DAY)
- **Clustering**: `clusterBy: ["ptag", "war_stars_var", "capital_contrib_var", "thl_var"]`
- **Unique Key**: `uniqueKey: ["extracted_date", "ptag"]`

### R2. Architectural Constraints & Logic Design
1. **Target Anchoring**: Utilize `${self()}` in a `target_anchor` CTE (`SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date FROM ${self()}`) for dynamic incremental state evaluation.
2. **7-Day Lookback Window**: Filter source data in `${ref("clan_members")}` using `extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)` to ensure `LAG()` window functions maintain calculation context across partition boundaries.
3. **Idempotent Insertion**: Apply outer `SELECT` filter `(war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0) AND extracted_date > (SELECT max_target_date FROM target_anchor)` in incremental mode (and `(war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0)` in full refresh mode).
4. **Data Quality Assertions & Cost Optimization**:
   - Unique key assertion on `["extracted_date", "ptag"]`.
   - Non-null assertions on `["extracted_date", "ptag", "war_stars_var", "capital_contrib_var", "thl_var"]`.
   - Complete column level documentation.
   - Omit global `ORDER BY` clause to avoid unneeded BigQuery execution cost.

### R3. Verification & Memory Recording
- Verify compilation with `pnpm dataform compile` targeting 0 errors across 42 compiled actions (14 datasets, 28 assertions).
- Register the architectural decision cornerstone into Nyutu memory via `save_cornerstone.py`.

## 3. Model Configuration Specification

```javascript
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag"],
  description: "Denormalized silver table tracking daily member stat progressions (war stars, capital contributions, town hall level) achieved by clan members.",
  tags: ["silver", "daily", "upgrades"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "war_stars_var", "capital_contrib_var", "thl_var"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag"],
    nonNull: ["extracted_date", "ptag", "war_stars_var", "capital_contrib_var", "thl_var"]
  },
  columns: {
    extracted_date: "Partitioning date when the member stat upgrade/progression was recorded.",
    prev_date: "Previous extraction date prior to the stat progression.",
    ptag: "Unique identifier tag of the player.",
    pname: "Player in-game display name.",
    current_war_stars: "Total war stars after progression.",
    prev_war_stars: "Total war stars prior to progression.",
    war_stars_var: "War stars gained since previous extraction date.",
    current_capital_contrib: "Total capital contributions after progression.",
    prev_capital_contrib: "Total capital contributions prior to progression.",
    capital_contrib_var: "Capital contributions gained since previous extraction date.",
    current_thl: "Town hall level after progression.",
    prev_thl: "Town hall level prior to progression.",
    thl_var: "Town hall levels gained since previous extraction date."
  }
}
```

## 4. SQLX Target & Non-Incremental Query Design

```sql
${when(incremental(), `
WITH target_anchor AS (
  SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
  FROM ${self()}
),

member_history AS (
  SELECT
    extracted_date,
    LAG(extracted_date, 1) OVER w_member AS prev_date,
    ptag,
    pname,
    war_stars AS current_war_stars,
    LAG(war_stars, 1) OVER w_member AS prev_war_stars,
    war_stars - LAG(war_stars, 1) OVER w_member AS war_stars_var,
    capital_contrib AS current_capital_contrib,
    LAG(capital_contrib, 1) OVER w_member AS prev_capital_contrib,
    capital_contrib - LAG(capital_contrib, 1) OVER w_member AS capital_contrib_var,
    thl AS current_thl,
    LAG(thl, 1) OVER w_member AS prev_thl,
    thl - LAG(thl, 1) OVER w_member AS thl_var
  FROM 
    ${ref("clan_members")}
  WHERE 
    extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
  WINDOW w_member AS (PARTITION BY ptag ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  pname,
  current_war_stars,
  prev_war_stars,
  war_stars_var,
  current_capital_contrib,
  prev_capital_contrib,
  capital_contrib_var,
  current_thl,
  prev_thl,
  thl_var
FROM 
  member_history
WHERE 
  (war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0)
  AND extracted_date > (SELECT max_target_date FROM target_anchor)
`)}

${when(!incremental(), `
WITH member_history AS (
  SELECT
    extracted_date,
    LAG(extracted_date, 1) OVER w_member AS prev_date,
    ptag,
    pname,
    war_stars AS current_war_stars,
    LAG(war_stars, 1) OVER w_member AS prev_war_stars,
    war_stars - LAG(war_stars, 1) OVER w_member AS war_stars_var,
    capital_contrib AS current_capital_contrib,
    LAG(capital_contrib, 1) OVER w_member AS prev_capital_contrib,
    capital_contrib - LAG(capital_contrib, 1) OVER w_member AS capital_contrib_var,
    thl AS current_thl,
    LAG(thl, 1) OVER w_member AS prev_thl,
    thl - LAG(thl, 1) OVER w_member AS thl_var
  FROM 
    ${ref("clan_members")}
  WINDOW w_member AS (PARTITION BY ptag ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  pname,
  current_war_stars,
  prev_war_stars,
  war_stars_var,
  current_capital_contrib,
  prev_capital_contrib,
  capital_contrib_var,
  current_thl,
  prev_thl,
  thl_var
FROM 
  member_history
WHERE 
  (war_stars_var > 0 OR capital_contrib_var > 0 OR thl_var > 0)
`)}
```

## 5. Step-by-Step Implementation Plan
- [x] **Task 1**: Draft implementation plan spec (`specs/coc-elt_20260802_clan_member_upgrades_implementation_plan.md`).
- [ ] **Task 2**: Draft walkthrough spec (`specs/coc-elt_20260802_clan_member_upgrades_walkthrough.md`).
- [ ] **Task 3**: Create Dataform SQLX model `definitions/clan_member_upgrades.sqlx`.
- [ ] **Task 4**: Execute `pnpm dataform compile` and verify 42 compiled actions.
- [ ] **Task 5**: Save Nyutu memory cornerstone entry.
- [ ] **Task 6**: Produce final handoff report in `.agents/worker_r1_1/handoff.md`.
