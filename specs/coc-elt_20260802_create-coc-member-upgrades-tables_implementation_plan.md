---
title: "Create coc_member Upgrade Tracking Models in coc_silver"
project_id: "coc-elt"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md"
---

## 1. User Intent & System Context
The objective is to implement three new incremental Dataform SQLX models in schema `coc_silver` for tracking daily level upgrades across member troops, hero equipment, and spells:
1. `definitions/coc_member_troops_upgrades.sqlx`
2. `definitions/coc_member_heroEquips_upgrades.sqlx`
3. `definitions/coc_member_spells_upgrades.sqlx`

These models must strictly replicate the established architectural design pattern used in `definitions/coc_member_hero_upgrades.sqlx`.

### Key Grounding Parameters
- Dataform Framework: `@dataform/core@2.9.0`
- Target Schema: `coc_silver`
- Assertion Schema: `coc_assertions`
- Default Database: `swift-capsule-492817-a7`

---

## 2. File Actions

| Action | Path | Description |
|--------|------|-------------|
| **Create** | `definitions/coc_member_troops_upgrades.sqlx` | Incremental silver table tracking daily troop level upgrades. |
| **Create** | `definitions/coc_member_heroEquips_upgrades.sqlx` | Incremental silver table tracking daily hero equipment level upgrades. |
| **Create** | `definitions/coc_member_spells_upgrades.sqlx` | Incremental silver table tracking daily spell level upgrades. |
| **Create** | `specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md` | Implementation plan specification document. |
| **Create** | `specs/coc-elt_20260802_create-coc-member-upgrades-tables_walkthrough.md` | Walkthrough specification document. |

---

## 3. Strict Architectural Constraints

Each of the three upgrade models MUST satisfy all four core architectural constraints derived from `coc_member_hero_upgrades.sqlx`:

1. **Target Anchoring (`${self()}`)**:
   - In incremental execution mode (`when(incremental())`), retrieve the current state watermark `max_target_date` directly from the target table itself using `${self()}`:
     ```sql
     WITH target_anchor AS (
       SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
       FROM ${self()}
     )
     ```
   - Avoid querying source tables for maximum target dates.

2. **Lookback Window for `LAG()` Context**:
   - Filter source silver tables (`coc_member_troops`, `coc_member_heroEquips`, `coc_member_spells`) using a 7-day lookback window:
     ```sql
     WHERE extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
     ```
   - This ensures `LAG(level, 1)` and `LAG(extracted_date, 1)` across window partition `(PARTITION BY ptag, <entity_key> ORDER BY extracted_date ASC)` have historical context across partition boundaries.

3. **Idempotent Incremental Insertion**:
   - In the outermost `SELECT` of the incremental block, filter output using:
     ```sql
     WHERE level_var > 0 AND extracted_date > (SELECT max_target_date FROM target_anchor)
     ```
   - Guaranteed single-append behaviour for newly processed partition dates without duplicating existing historical records.

4. **Cost, Clustering & Data Quality Standards**:
   - Omit global `ORDER BY` clauses to eliminate unnecessary BigQuery sorting costs.
   - Partitioning: `partitionBy: "extracted_date"` (DAY).
   - Clustering: `clusterBy: ["ptag", "<entity_key>"]`.
   - Data quality assertions: `uniqueKey` on `["extracted_date", "ptag", "<entity_key>"]` and `nonNull` on `["extracted_date", "ptag", "<entity_key>", "current_level", "prev_level"]`.
   - Complete `columns` documentation in the SQLX `config` block.

---

## 4. Requirements & Model Design Specifications

### R1. Troop Upgrades Model (`definitions/coc_member_troops_upgrades.sqlx`)
- **Source Table**: `${ref("coc_member_troops")}`
- **Entity Key**: `troop_name`
- **Source Level Column**: `troop_level`
- **Target Table Name**: `coc_silver.coc_member_troops_upgrades`
- **Unique Key / Assertion**: `["extracted_date", "ptag", "troop_name"]`
- **Clustering**: `["ptag", "troop_name"]`

#### SQLX Specification:
```javascript
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "troop_name"],
  description: "Denormalized silver table tracking daily troop level upgrades achieved by clan members.",
  tags: ["silver", "daily", "upgrades"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "troop_name"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "troop_name"],
    nonNull: ["extracted_date", "ptag", "troop_name", "current_level", "prev_level"]
  },
  columns: {
    extracted_date: "Partitioning date when the troop upgrade was recorded.",
    prev_date: "Previous extraction date prior to the upgrade.",
    ptag: "Unique identifier tag of the player.",
    troop_name: "Name of the troop (e.g. Barbarian, Archer).",
    current_level: "Troop level achieved after the upgrade.",
    prev_level: "Troop level prior to the upgrade.",
    level_var: "Number of levels gained in this upgrade."
  }
}

${when(incremental(), `
WITH target_anchor AS (
  SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
  FROM ${self()}
),

troops_history AS (
  SELECT
    extracted_date,
    ptag,
    troop_name,
    troop_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(troop_level, 1) OVER w_equip AS prev_level,
    troop_level - LAG(troop_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_troops")}
  WHERE 
    extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
  WINDOW w_equip AS (PARTITION BY ptag, troop_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  troop_name,
  current_level,
  prev_level,
  level_var
FROM 
  troops_history
WHERE 
  level_var > 0
  AND extracted_date > (SELECT max_target_date FROM target_anchor)
`)}

${when(!incremental(), `
WITH troops_history AS (
  SELECT
    extracted_date,
    ptag,
    troop_name,
    troop_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(troop_level, 1) OVER w_equip AS prev_level,
    troop_level - LAG(troop_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_troops")}
  WINDOW w_equip AS (PARTITION BY ptag, troop_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  troop_name,
  current_level,
  prev_level,
  level_var
FROM 
  troops_history
WHERE 
  level_var > 0
`)}
```

---

### R2. Hero Equipment Upgrades Model (`definitions/coc_member_heroEquips_upgrades.sqlx`)
- **Source Table**: `${ref("coc_member_heroEquips")}`
- **Entity Key**: `equipment_name`
- **Source Level Column**: `equipment_level`
- **Target Table Name**: `coc_silver.coc_member_heroEquips_upgrades`
- **Unique Key / Assertion**: `["extracted_date", "ptag", "equipment_name"]`
- **Clustering**: `["ptag", "equipment_name"]`

#### SQLX Specification:
```javascript
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "equipment_name"],
  description: "Denormalized silver table tracking daily hero equipment level upgrades achieved by clan members.",
  tags: ["silver", "daily", "upgrades"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "equipment_name"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "equipment_name"],
    nonNull: ["extracted_date", "ptag", "equipment_name", "current_level", "prev_level"]
  },
  columns: {
    extracted_date: "Partitioning date when the hero equipment upgrade was recorded.",
    prev_date: "Previous extraction date prior to the upgrade.",
    ptag: "Unique identifier tag of the player.",
    equipment_name: "Name of the hero equipment (e.g. Giant Gauntlet, Frozen Arrow).",
    current_level: "Hero equipment level achieved after the upgrade.",
    prev_level: "Hero equipment level prior to the upgrade.",
    level_var: "Number of levels gained in this upgrade."
  }
}

${when(incremental(), `
WITH target_anchor AS (
  SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
  FROM ${self()}
),

hero_equips_history AS (
  SELECT
    extracted_date,
    ptag,
    equipment_name,
    equipment_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(equipment_level, 1) OVER w_equip AS prev_level,
    equipment_level - LAG(equipment_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_heroEquips")}
  WHERE 
    extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
  WINDOW w_equip AS (PARTITION BY ptag, equipment_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  equipment_name,
  current_level,
  prev_level,
  level_var
FROM 
  hero_equips_history
WHERE 
  level_var > 0
  AND extracted_date > (SELECT max_target_date FROM target_anchor)
`)}

${when(!incremental(), `
WITH hero_equips_history AS (
  SELECT
    extracted_date,
    ptag,
    equipment_name,
    equipment_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(equipment_level, 1) OVER w_equip AS prev_level,
    equipment_level - LAG(equipment_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_heroEquips")}
  WINDOW w_equip AS (PARTITION BY ptag, equipment_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  equipment_name,
  current_level,
  prev_level,
  level_var
FROM 
  hero_equips_history
WHERE 
  level_var > 0
`)}
```

---

### R3. Spell Upgrades Model (`definitions/coc_member_spells_upgrades.sqlx`)
- **Source Table**: `${ref("coc_member_spells")}`
- **Entity Key**: `spell_name`
- **Source Level Column**: `spell_level`
- **Target Table Name**: `coc_silver.coc_member_spells_upgrades`
- **Unique Key / Assertion**: `["extracted_date", "ptag", "spell_name"]`
- **Clustering**: `["ptag", "spell_name"]`

#### SQLX Specification:
```javascript
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "spell_name"],
  description: "Denormalized silver table tracking daily spell level upgrades achieved by clan members.",
  tags: ["silver", "daily", "upgrades"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "spell_name"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "spell_name"],
    nonNull: ["extracted_date", "ptag", "spell_name", "current_level", "prev_level"]
  },
  columns: {
    extracted_date: "Partitioning date when the spell upgrade was recorded.",
    prev_date: "Previous extraction date prior to the upgrade.",
    ptag: "Unique identifier tag of the player.",
    spell_name: "Name of the spell (e.g. Lightning Spell, Healing Spell).",
    current_level: "Spell level achieved after the upgrade.",
    prev_level: "Spell level prior to the upgrade.",
    level_var: "Number of levels gained in this upgrade."
  }
}

${when(incremental(), `
WITH target_anchor AS (
  SELECT COALESCE(MAX(extracted_date), DATE('1970-01-01')) AS max_target_date
  FROM ${self()}
),

spells_history AS (
  SELECT
    extracted_date,
    ptag,
    spell_name,
    spell_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(spell_level, 1) OVER w_equip AS prev_level,
    spell_level - LAG(spell_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_spells")}
  WHERE 
    extracted_date >= DATE_SUB((SELECT max_target_date FROM target_anchor), INTERVAL 7 DAY)
  WINDOW w_equip AS (PARTITION BY ptag, spell_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  spell_name,
  current_level,
  prev_level,
  level_var
FROM 
  spells_history
WHERE 
  level_var > 0
  AND extracted_date > (SELECT max_target_date FROM target_anchor)
`)}

${when(!incremental(), `
WITH spells_history AS (
  SELECT
    extracted_date,
    ptag,
    spell_name,
    spell_level AS current_level,
    LAG(extracted_date, 1) OVER w_equip AS prev_date,
    LAG(spell_level, 1) OVER w_equip AS prev_level,
    spell_level - LAG(spell_level, 1) OVER w_equip AS level_var
  FROM 
    ${ref("coc_member_spells")}
  WINDOW w_equip AS (PARTITION BY ptag, spell_name ORDER BY extracted_date ASC)
)

SELECT 
  extracted_date,
  prev_date,
  ptag,
  spell_name,
  current_level,
  prev_level,
  level_var
FROM 
  spells_history
WHERE 
  level_var > 0
`)}
```

---

## 5. Verification Plan

### Step 1: Dataform AST Compilation Verification
- Command:
  ```bash
  pnpm dataform compile
  ```
- Execution Directory: `/home/scheveningen/documents/proyectos/coc_elt`
- Expected Outcome:
  - Exit code `0` (Zero compilation errors).
  - Total compiled actions increases from baseline 30 actions to 39 actions (13 datasets + 26 assertions).
  - Validation of dataset references `${ref("...")}`, BigQuery configuration options (`partitionBy`, `clusterBy`), uniqueKey constraints, and nonNull assertions.

### Step 2: Nyutu Architectural Memory Ingestion
- Command:
  ```bash
  uv run --project /home/scheveningen/.gemini/config/plugins/cerelino/skills/nyutu-mng/commands \
    /home/scheveningen/.gemini/config/plugins/cerelino/skills/nyutu-mng/commands/save_cornerstone.py \
    --title "Create Member Troops, HeroEquips, and Spells Upgrades Tables in coc_silver" \
    --artifact-type "Infrastructure Pattern" \
    --content "Pattern implementation of coc_member_troops_upgrades, coc_member_heroEquips_upgrades, and coc_member_spells_upgrades incremental tables using target anchoring (${self()}), 7-day lookback window, LAG() windowing, and idempotent insertion." \
    --project-id "coc-elt" \
    --source-uri "specs/coc-elt_20260802_create-coc-member-upgrades-tables_implementation_plan.md"
  ```
- Expected Outcome: Cornerstone successfully persisted to project `coc-elt` memory database.
