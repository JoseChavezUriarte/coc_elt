---
title: "Add War Attributes to wars Implementation Plan"
project_id: "coc-elt"
nyutu_uuid: "2a6a21a7-5673-45ac-989b-fbb703eec4cb"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260721_add-war-attributes_implementation_plan.md"
---

# Implementation Plan - Add War-Level and Member-Level Attributes to `definitions/wars.sqlx` (Revised with Member Attributes)

This document details the revised implementation plan to introduce 8 war-level attributes and 3 new member-level attributes (`mapPosition`, `opponentAttacks`, and `townhallLevel`) into the silver denormalized table defined by `definitions/wars.sqlx` and convert columns ending in 'Time' to `DATETIME` objects.

---

## 1. Existing System Context
The file `definitions/wars.sqlx` defines an incremental Dataform table `coc_silver.wars` that lists individual player attacks in clan wars. Each row represents an attack and includes metadata about the war (such as `state` and `teamSize`). 

The new attributes are war-level and member-level attributes. In a denormalized silver table where each row represents an attack, these attributes will be broadcasted (duplicated) across all attacks belonging to the same war payload.

To simplify the schema and avoid sparse/redundant columns, we map the clan level, destruction percentage, and stars to single unified columns (`clanLevel`, `clanDestructionPct`, `clanStars`). These columns will represent the statistics of the *attacking member's clan* based on whether they belong to the home clan (`member_type = 'clan'`) or the opponent clan (`member_type = 'opponent'`).

---

## 2. Requirements (EARS Notation)
- **R1 (Table Config Documentation)**: When the Dataform table `coc_silver.wars` is compiled, its configuration block **shall** document all the new columns (`clanLevel`, `clanDestructionPct`, `clanStars`, `attacksPerMember`, `battleModifier`, `preparationStartTime`, `startTime`, `endTime`, `mapPosition`, `opponentAttacks`, and `townhallLevel`) and omit any redundant/removed columns.
- **R2 (Attribute Projection)**: Both the `clan_attacks` and `opponent_attacks` subqueries **shall** project the 8 war-level and 3 member-level columns using the specified payload extraction logic and cast statements.
- **R3 (Redundant Column Exclusion)**: The final table and subqueries **shall not** project the redundant columns `opponentClanLevel`, `opponentDestructionPct`, and `opponentStars`.
- **R4 (Numeric Safety)**: The columns `clanLevel`, `clanStars`, `attacksPerMember`, `clanDestructionPct`, `mapPosition`, `opponentAttacks`, and `townhallLevel` **shall** be extracted using `SAFE_CAST` to safeguard against invalid or missing values in raw JSON payloads.
- **R5 (Datetime Casts)**: The columns `preparationStartTime`, `startTime`, and `endTime` **shall** be extracted using `SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(...)) AS DATETIME)` to correctly parse timezone-aware compact ISO timestamps returned by the API into naive DATETIME objects.
- **R6 (Compilation)**: When compiling the Dataform project locally, the compiler **shall** execute successfully without schema or SQL errors.

---

## 3. Technical Decisions & Trade-offs
- **Decision 1 (Consolidation of Clan-level Attributes)**: Instead of projecting separate columns for `clanLevel` and `opponentClanLevel` (which would result in high sparsity and redundant columns), we project a single column `clanLevel` representing the level of the attacking member's clan (`payload.clan.clanLevel` for `member_type = 'clan'` and `payload.opponent.clanLevel` for `member_type = 'opponent'`).
  * **Pros**: Avoids NULL-heavy redundant columns, simplifies analytics on attacker clans, matches the `member_type` logic.
  * **Cons**: If users want to query the opponent clan's level of a given attack in a single row without joins, they must use the opponent's tag to lookup. However, since every attack has an opposing member tag, this is easily done.
- **Decision 2 (Float Precision for Destruction)**: `destruction_percentage` of an individual attack is an integer (`INT64`), but the overall clan destruction percentage `destructionPercentage` in the payload is a percentage/decimal representing cumulative damage, which we cast to `FLOAT64` as `clanDestructionPct`.
- **Decision 3 (Datetime Cast Strategy)**: Parse with `SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(...))` and cast with `SAFE_CAST(... AS DATETIME)`. `SAFE.PARSE_TIMESTAMP` handles timezone designator `'Z'` natively and avoids compilation/runtime errors if strings are malformed. `SAFE_CAST(... AS DATETIME)` projects the timestamp to a timezone-naive `DATETIME` corresponding to the UTC values in the source.
- **Decision 4 (Member-Level Extraction)**: Extract `mapPosition`, `opponentAttacks`, and `townhallLevel` from the unnested `member` JSON object since they represent attacker properties in the context of the war.

---

## 4. File Specifications & Templates

### File: `definitions/wars.sqlx`

```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "defender_tag"],
  description: "Denormalized and deduplicated silver table containing clan war attacks.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["extracted_date", "ptag", "state", "teamSize"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "defender_tag"],
    nonNull: ["extracted_date", "ptag", "defender_tag"]
  },
  columns: {
    extracted_at: "Timestamp when the war payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player performing the attack.",
    defender_tag: "Unique identifier tag of the player being defended.",
    state: "The current state of the war (e.g. preparation, inWar, warEnded).",
    teamSize: "The size of the teams in the war.",
    war_clan_tag: "Tag of the home clan.",
    war_opponent_tag: "Tag of the opponent clan.",
    member_tag: "Tag of the member who performed the attack.",
    member_name: "In-game name of the member who performed the attack.",
    member_type: "Role of the member's clan in the war ('clan' or 'opponent').",
    stars: "Number of stars scored in the attack.",
    destruction_percentage: "Destruction percentage achieved in the attack.",
    attack_order: "Chronological order of the attack in the war.",
    duration: "Duration of the attack in seconds.",
    clanLevel: "Level of the clan of the member performing the attack.",
    clanDestructionPct: "Total destruction percentage achieved by the clan of the member performing the attack.",
    clanStars: "Total stars scored by the clan of the member performing the attack.",
    attacksPerMember: "Number of allowed attacks per member in the war.",
    battleModifier: "The battle modifier applied to the war (e.g. hardMode).",
    preparationStartTime: "DATETIME representation of the preparation start time.",
    startTime: "DATETIME representation of the war start time.",
    endTime: "DATETIME representation of the war end time.",
    mapPosition: "Map position of the attacking player in the war.",
    opponentAttacks: "Number of attacks received by the attacking player in this war.",
    townhallLevel: "Town Hall level of the attacking player."
  }
}

WITH latest_war_payloads AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    payload
  FROM
    ${ref("coc_current_war")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY
      DATE(extracted_at),
      JSON_VALUE(payload.clan.tag),
      JSON_VALUE(payload.opponent.tag)
    ORDER BY
      extracted_at DESC
  ) = 1
),

clan_attacks AS (
  SELECT
    extracted_at,
    extracted_date,
    JSON_VALUE(payload.state) AS state,
    SAFE_CAST(JSON_VALUE(payload.teamSize) AS INT64) AS teamSize,
    JSON_VALUE(payload.clan.tag) AS war_clan_tag,
    JSON_VALUE(payload.opponent.tag) AS war_opponent_tag,
    JSON_VALUE(member.tag) AS member_tag,
    JSON_VALUE(member.name) AS member_name,
    'clan' AS member_type,
    JSON_VALUE(attack.attackerTag) AS ptag,
    JSON_VALUE(attack.defenderTag) AS defender_tag,
    SAFE_CAST(JSON_VALUE(attack.stars) AS INT64) AS stars,
    SAFE_CAST(JSON_VALUE(attack.destructionPercentage) AS INT64) AS destruction_percentage,
    SAFE_CAST(JSON_VALUE(attack.order) AS INT64) AS attack_order,
    SAFE_CAST(JSON_VALUE(attack.duration) AS INT64) AS duration,
    SAFE_CAST(JSON_VALUE(payload.clan.clanLevel) AS INT64) AS clanLevel,
    SAFE_CAST(JSON_VALUE(payload.clan.destructionPercentage) AS FLOAT64) AS clanDestructionPct,
    SAFE_CAST(JSON_VALUE(payload.clan.stars) AS INT64) AS clanStars,
    SAFE_CAST(JSON_VALUE(payload.attacksPerMember) AS INT64) AS attacksPerMember,
    JSON_VALUE(payload.battleModifier) AS battleModifier,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.preparationStartTime)) AS DATETIME) AS preparationStartTime,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.startTime)) AS DATETIME) AS startTime,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.endTime)) AS DATETIME) AS endTime,
    SAFE_CAST(JSON_VALUE(member.mapPosition) AS INT64) AS mapPosition,
    SAFE_CAST(JSON_VALUE(member.opponentAttacks) AS INT64) AS opponentAttacks,
    SAFE_CAST(JSON_VALUE(member.townhallLevel) AS INT64) AS townhallLevel
  FROM
    latest_war_payloads,
    UNNEST(JSON_QUERY_ARRAY(payload.clan.members)) AS member,
    UNNEST(JSON_QUERY_ARRAY(member.attacks)) AS attack
),

opponent_attacks AS (
  SELECT
    extracted_at,
    extracted_date,
    JSON_VALUE(payload.state) AS state,
    SAFE_CAST(JSON_VALUE(payload.teamSize) AS INT64) AS teamSize,
    JSON_VALUE(payload.clan.tag) AS war_clan_tag,
    JSON_VALUE(payload.opponent.tag) AS war_opponent_tag,
    JSON_VALUE(member.tag) AS member_tag,
    JSON_VALUE(member.name) AS member_name,
    'opponent' AS member_type,
    JSON_VALUE(attack.attackerTag) AS ptag,
    JSON_VALUE(attack.defenderTag) AS defender_tag,
    SAFE_CAST(JSON_VALUE(attack.stars) AS INT64) AS stars,
    SAFE_CAST(JSON_VALUE(attack.destructionPercentage) AS INT64) AS destruction_percentage,
    SAFE_CAST(JSON_VALUE(attack.order) AS INT64) AS attack_order,
    SAFE_CAST(JSON_VALUE(attack.duration) AS INT64) AS duration,
    SAFE_CAST(JSON_VALUE(payload.opponent.clanLevel) AS INT64) AS clanLevel,
    SAFE_CAST(JSON_VALUE(payload.opponent.destructionPercentage) AS FLOAT64) AS clanDestructionPct,
    SAFE_CAST(JSON_VALUE(payload.opponent.stars) AS INT64) AS clanStars,
    SAFE_CAST(JSON_VALUE(payload.attacksPerMember) AS INT64) AS attacksPerMember,
    JSON_VALUE(payload.battleModifier) AS battleModifier,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.preparationStartTime)) AS DATETIME) AS preparationStartTime,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.startTime)) AS DATETIME) AS startTime,
    SAFE_CAST(SAFE.PARSE_TIMESTAMP('%Y%m%dT%H%M%E*SZ', JSON_VALUE(payload.endTime)) AS DATETIME) AS endTime,
    SAFE_CAST(JSON_VALUE(member.mapPosition) AS INT64) AS mapPosition,
    SAFE_CAST(JSON_VALUE(member.opponentAttacks) AS INT64) AS opponentAttacks,
    SAFE_CAST(JSON_VALUE(member.townhallLevel) AS INT64) AS townhallLevel
  FROM
    latest_war_payloads,
    UNNEST(JSON_QUERY_ARRAY(payload.opponent.members)) AS member,
    UNNEST(JSON_QUERY_ARRAY(member.attacks)) AS attack
),

unioned_attacks AS (
  SELECT * FROM clan_attacks
  UNION ALL
  SELECT * FROM opponent_attacks
)

SELECT
  extracted_at,
  extracted_date,
  ptag,
  defender_tag,
  state,
  teamSize,
  war_clan_tag,
  war_opponent_tag,
  member_tag,
  member_name,
  member_type,
  stars,
  destruction_percentage,
  attack_order,
  duration,
  clanLevel,
  clanDestructionPct,
  clanStars,
  attacksPerMember,
  battleModifier,
  preparationStartTime,
  startTime,
  endTime,
  mapPosition,
  opponentAttacks,
  townhallLevel
FROM
  unioned_attacks
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY extracted_date, ptag, defender_tag
  ORDER BY extracted_at DESC, attack_order DESC
) = 1
```

---

## 5. Implementation Tasks
- [x] **T1**: Update the configuration block of `definitions/wars.sqlx` to declare the 3 new columns and their corresponding documentation descriptions.
- [x] **T2**: Modify the `clan_attacks` CTE subquery to extract and alias the 3 member-level fields using `member` with safe casts.
- [x] **T3**: Modify the `opponent_attacks` CTE subquery to extract and alias the 3 member-level fields using `member` with safe casts.
- [x] **T4**: Update the final SELECT projection query block to select the 3 new fields from `unioned_attacks`.
- [x] **T5**: Compile the Dataform project using the Dataform CLI (`pnpm exec dataform compile`) to verify syntax, column descriptions, and output schemas locally. Do NOT run git push or trigger GCP workflows.
