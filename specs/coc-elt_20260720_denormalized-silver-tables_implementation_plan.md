---
title: "Denormalized Incremental Dataform Tables for coc_silver"
project_id: "coc-elt"
nyutu_uuid: "acbcd50e-47ec-46a2-8839-82659ea4f929"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260720_denormalized-silver-tables_implementation_plan.md"
---

# Implementation Plan - Denormalized Incremental Dataform Tables for coc_silver (Revised)

This plan outlines the design and step-by-step implementation for 5 new denormalized, incremental Dataform tables in the `coc_silver` schema, querying `coc_bronze.coc_members`.

---

## 1. System Grounding & Context
- Source: `coc_bronze.coc_members` declared in [sources.js](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/sources.js).
- Target Schema: `coc_silver`.
- Design Pattern: Derived from [clan_members.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/clan_members.sqlx).
- Partitioning: Partitioned on `extracted_date` to align with the pattern in `clan_members.sqlx`.
- Incremental Logic: Only processes the last 2 days during incremental runs to reduce BigQuery costs.
- Deduplication Level 1 (Player Day Level): Deduplicates players at the daily level to keep only the latest record of each day for each player before unnesting.
- Deduplication Level 2 (Array Element Level): Immediately after the UNNEST clause in the final SELECT block, a `QUALIFY` clause is applied to resolve duplicates of the unnested items (e.g. same achievement, troop, spell, hero, or equipment on the same day for a player) by keeping the highest level/value.

---

## 2. Requirements (EARS Notation)
- **R1 (Incremental Processing)**: While the pipeline is running in incremental mode, the Dataform compiler shall filter the source query using `extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))`.
- **R2 (Target Merging)**: While in incremental mode, the Dataform compiler shall apply `updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"` to optimize target table merges.
- **R3 (Daily Player Deduplication)**: The Dataform query shall deduplicate the source records by partitioning on `DATE(extracted_at)` (using alias `extracted_date`) and player tag (`ptag`), ordering by `extracted_at DESC`, keeping only the first ranked record (the latest update of the day for each player) before unnesting.
- **R4 (Partitioning)**: The target tables shall be partitioned by `extracted_date` (using `partitionBy: "extracted_date"`).
- **R5 (Clustering)**: The target tables shall be clustered by their requested fields to optimize analytical queries.
- **R6 (Validation)**: The Dataform compiler shall generate validation assertions verifying that `ptag` and `extracted_date` are non-null, and that the combined unique key of the table is unique.
- **R7 (Array Element Deduplication)**: Immediately after the UNNEST clause in the final SELECT block of each of the 5 tables, the query shall apply a second layer of deduplication using the `QUALIFY` clause with `ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, [item_name] ORDER BY [item_level_or_value] DESC) = 1` to guarantee duplicate entries within raw payload arrays do not violate unique constraints.

---

## 3. Technical Decisions & Trade-offs
### Deduplication & Unnesting Order
- **Option A (Unnest First, Deduplicate Later)**: Unnest the arrays directly from `coc_bronze.coc_members`, then deduplicate the unnested records.
  - *Pros*: Simple query.
  - *Cons*: Very inefficient. Unnests rows that are eventually discarded, increasing CPU and memory consumption.
- **Option B (Two-Stage Deduplication - RECOMMENDED)**:
  1. Filter and rank the player records first, keeping the latest record of the day (`deduped_members` CTE).
  2. Unnest the arrays from that latest record.
  3. Apply a `QUALIFY` clause immediately after the UNNEST operation to keep only the highest level/value of any duplicated item for that user on that day.
  - *Pros*: Highly efficient. Minimizes the volume of data passed to the unnesting step while guaranteeing unique constraint safety.
  - *Cons*: Requires staging CTEs and an additional window function at the end.
  - *Decision*: **Option B** is chosen for performance, FinOps optimization, and constraint enforcement.

---

## 4. File Specifications & Templates

All files will be created in the `definitions/` directory.

### New Files to Create:
1. `definitions/coc_member_achievements.sqlx`
2. `definitions/coc_member_heroEquips.sqlx`
3. `definitions/coc_member_hero.sqlx`
4. `definitions/coc_member_spells.sqlx`
5. `definitions/coc_member_troops.sqlx`

---

### SQLX Templates

#### 1. [coc_member_achievements.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_achievements.sqlx)
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "achievement_name"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "achievement_name", "achievement_village", "achievement_stars"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "achievement_name"],
    nonNull: ["extracted_date", "ptag"]
  }
}

WITH parsed_members AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS ptag,
    payload.achievements AS achievements
  FROM
    ${ref("coc_members")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
),

deduped_members AS (
  SELECT
    extracted_at,
    extracted_date,
    ptag,
    achievements
  FROM
    ranked_members
  WHERE
    row_num = 1
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  JSON_VALUE(achievement.name) AS achievement_name,
  SAFE_CAST(JSON_VALUE(achievement.stars) AS INT64) AS achievement_stars,
  SAFE_CAST(JSON_VALUE(achievement.value) AS INT64) AS achievement_value,
  SAFE_CAST(JSON_VALUE(achievement.target) AS INT64) AS achievement_target,
  JSON_VALUE(achievement.village) AS achievement_village
FROM
  deduped_members,
  UNNEST(JSON_QUERY_ARRAY(achievements)) AS achievement
QUALIFY ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, achievement_name ORDER BY achievement_value DESC) = 1
```

---

#### 2. [coc_member_heroEquips.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_heroEquips.sqlx)
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "equipment_name"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "equipment_village", "equipment_name", "equipment_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "equipment_name"],
    nonNull: ["extracted_date", "ptag"]
  }
}

WITH parsed_members AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS ptag,
    payload.heroEquipment AS hero_equipment
  FROM
    ${ref("coc_members")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
),

deduped_members AS (
  SELECT
    extracted_at,
    extracted_date,
    ptag,
    hero_equipment
  FROM
    ranked_members
  WHERE
    row_num = 1
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  JSON_VALUE(equip.name) AS equipment_name,
  SAFE_CAST(JSON_VALUE(equip.level) AS INT64) AS equipment_level,
  SAFE_CAST(JSON_VALUE(equip.maxLevel) AS INT64) AS equipment_max_level,
  JSON_VALUE(equip.village) AS equipment_village
FROM
  deduped_members,
  UNNEST(JSON_QUERY_ARRAY(hero_equipment)) AS equip
QUALIFY ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, equipment_name ORDER BY equipment_level DESC) = 1
```

---

#### 3. [coc_member_hero.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_hero.sqlx)
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "hero_name"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "hero_village", "hero_name", "hero_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "hero_name"],
    nonNull: ["extracted_date", "ptag"]
  }
}

WITH parsed_members AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS ptag,
    payload.heroes AS heroes
  FROM
    ${ref("coc_members")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
),

deduped_members AS (
  SELECT
    extracted_at,
    extracted_date,
    ptag,
    heroes
  FROM
    ranked_members
  WHERE
    row_num = 1
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  JSON_VALUE(hero.name) AS hero_name,
  SAFE_CAST(JSON_VALUE(hero.level) AS INT64) AS hero_level,
  SAFE_CAST(JSON_VALUE(hero.maxLevel) AS INT64) AS hero_max_level,
  JSON_VALUE(hero.village) AS hero_village
FROM
  deduped_members,
  UNNEST(JSON_QUERY_ARRAY(heroes)) AS hero
QUALIFY ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, hero_name ORDER BY hero_level DESC) = 1
```

---

#### 4. [coc_member_spells.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_spells.sqlx)
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "spell_name"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "spell_village", "spell_name", "spell_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "spell_name"],
    nonNull: ["extracted_date", "ptag"]
  }
}

WITH parsed_members AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS ptag,
    payload.spells AS spells
  FROM
    ${ref("coc_members")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
),

deduped_members AS (
  SELECT
    extracted_at,
    extracted_date,
    ptag,
    spells
  FROM
    ranked_members
  WHERE
    row_num = 1
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  JSON_VALUE(spell.name) AS spell_name,
  SAFE_CAST(JSON_VALUE(spell.level) AS INT64) AS spell_level,
  SAFE_CAST(JSON_VALUE(spell.maxLevel) AS INT64) AS spell_max_level,
  JSON_VALUE(spell.village) AS spell_village
FROM
  deduped_members,
  UNNEST(JSON_QUERY_ARRAY(spells)) AS spell
QUALIFY ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, spell_name ORDER BY spell_level DESC) = 1
```

---

#### 5. [coc_member_troops.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_troops.sqlx)
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "troop_name"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "troop_village", "troop_name", "troop_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "troop_name"],
    nonNull: ["extracted_date", "ptag"]
  }
}

WITH parsed_members AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS ptag,
    payload.troops AS troops
  FROM
    ${ref("coc_members")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
),

deduped_members AS (
  SELECT
    extracted_at,
    extracted_date,
    ptag,
    troops
  FROM
    ranked_members
  WHERE
    row_num = 1
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  JSON_VALUE(troop.name) AS troop_name,
  SAFE_CAST(JSON_VALUE(troop.level) AS INT64) AS troop_level,
  SAFE_CAST(JSON_VALUE(troop.maxLevel) AS INT64) AS troop_max_level,
  JSON_VALUE(troop.village) AS troop_village
FROM
  deduped_members,
  UNNEST(JSON_QUERY_ARRAY(troops)) AS troop
QUALIFY ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag, troop_name ORDER BY troop_level DESC) = 1
```

---

## 5. Implementation Tasks

- **T1: Create achievements SQLX file**
  - Create `definitions/coc_member_achievements.sqlx` with the specified template.
  - Verification: Run `pnpm exec dataform compile` and verify successful compilation without errors.
- **T2: Create heroEquips SQLX file**
  - Create `definitions/coc_member_heroEquips.sqlx` with the specified template.
  - Verification: Run `pnpm exec dataform compile` and verify successful compilation.
- **T3: Create hero SQLX file**
  - Create `definitions/coc_member_hero.sqlx` with the specified template.
  - Verification: Run `pnpm exec dataform compile` and verify successful compilation.
- **T4: Create spells SQLX file**
  - Create `definitions/coc_member_spells.sqlx` with the specified template.
  - Verification: Run `pnpm exec dataform compile` and verify successful compilation.
- **T5: Create troops SQLX file**
  - Create `definitions/coc_member_troops.sqlx` with the specified template.
  - Verification: Run `pnpm exec dataform compile` and verify successful compilation.
- **T6: Compilation Verification**
  - Run `pnpm exec dataform compile` in the repository root to verify all 5 new models compile successfully.
