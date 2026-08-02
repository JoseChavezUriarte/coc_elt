---
title: "Create coc_member_hero_upgrades Table in coc_silver"
project_id: "coc-elt"
nyutu_uuid: "b133af9e-9a42-4bcd-a97a-e59447e3adc6"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_implementation_plan.md"
---

## 1. System Context & Codebase Grounding
- Target dataset/schema: `coc_silver`
- Model Name: `coc_member_hero_upgrades`
- Source table reference: `${ref("coc_member_hero")}`
- Self reference target: `${self()}`

## 2. File Actions
- **Create File:** `definitions/coc_member_hero_upgrades.sqlx` under `/home/scheveningen/documents/proyectos/coc_elt`
  - Purpose: Define the `coc_member_hero_upgrades` incremental model in Dataform.

## 3. Strict Architectural Constraints
- **C1 (Target Anchoring via `${self()}`)**: Remove `date_bounds` source queries. Retrieve `max_target_date` directly from target table using `${self()}` in incremental runs (`SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) FROM ${self()}`).
- **C2 (Lookback Window for `LAG()`)**: Filter source `${ref("coc_member_hero")}` to `extracted_date >= DATE_SUB(max_target_date, INTERVAL 7 DAY)` to ensure `LAG()` receives necessary historical context across partition boundaries.
- **C3 (Idempotent Insertion)**: Apply `extracted_date > max_target_date` filter in the final `SELECT` statement to guarantee only strictly new records are appended.
- **C4 (Cost & Metadata Optimization)**:
  - Remove global `ORDER BY` clause.
  - Set `clusterBy: ["ptag", "hero_name"]` and retain `partitionBy: "extracted_date"`.

## 4. Requirements (EARS Notation)
- **R1 (Incremental Materialization & Target Schema)**: Configured in `coc_silver` as an `incremental` materialization type.
- **R2 (Unique Key Constraint)**: Define `uniqueKey` as `["extracted_date", "ptag", "hero_name"]`.
- **R3 (Partitioning & Clustering)**: `partitionBy: "extracted_date"` (DAY) and `clusterBy: ["ptag", "hero_name"]`.
- **R4 (Data Quality Assertions)**: Assertions for `uniqueKey` and `nonNull` on key attributes `["extracted_date", "ptag", "hero_name", "current_level", "prev_level"]`.

## 5. SQLX Code Template

```javascript
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "hero_name"],
  description: "Denormalized silver table tracking daily hero level upgrades achieved by clan members.",
  tags: ["silver", "daily", "upgrades"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "hero_name"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "hero_name"],
    nonNull: ["extracted_date", "ptag", "hero_name", "current_level", "prev_level"]
  },
  columns: {
    extracted_date: "Partitioning date when the hero upgrade was recorded.",
    prev_date: "Previous extraction date prior to the upgrade.",
    ptag: "Unique identifier tag of the player.",
    hero_name: "Name of the hero (e.g. Barbarian King, Archer Queen).",
    current_level: "Hero level achieved after the upgrade.",
    prev_level: "Hero level prior to the upgrade.",
    level_var: "Number of levels gained in this upgrade."
  }
}

${when(incremental(), `
WITH target_anchor AS (
  SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
  FROM ${self()}
),

hero_history AS (
  SELECT
    extracted_date,
    ptag,
    hero_name,
    hero_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(hero_level, 1) OVER w_equip AS prev_level,
    hero_level - LAG(hero_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_hero")}
  WHERE 
    extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
  WINDOW w_equip AS (PARTITION BY ptag, hero_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  hero_name,
  current_level,
  prev_level,
  level_var
FROM 
  hero_history
WHERE 
  level_var > 0
  AND extracted_date > (SELECT max_target_date FROM target_anchor)
`)}

${when(!incremental(), `
WITH hero_history AS (
  SELECT
    extracted_date,
    ptag,
    hero_name,
    hero_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(hero_level, 1) OVER w_equip AS prev_level,
    hero_level - LAG(hero_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_hero")}
  WINDOW w_equip AS (PARTITION BY ptag, hero_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  hero_name,
  current_level,
  prev_level,
  level_var
FROM 
  hero_history
WHERE 
  level_var > 0
`)}
```

## 6. Implementation & Verification Steps
- [ ] **T1:** Create `definitions/coc_member_hero_upgrades.sqlx` with the updated template.
- [ ] **T2:** Verify Dataform compilation locally (`pnpm dataform compile`).
- [ ] **T3:** Create walkthrough document [`specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_walkthrough.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260802_create-coc-member-hero-upgrades-table_walkthrough.md).
