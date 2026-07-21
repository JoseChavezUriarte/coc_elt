---
title: "Create wars Table in coc_silver Implementation Plan"
project_id: "coc-elt"
nyutu_uuid: "34074d2c-2a17-40ce-b391-e07a8008d1a8"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260721_create-wars-table_implementation_plan.md"
---

# Implementation Plan: Dataform Silver Model for `coc_silver.wars`

This implementation plan outlines the architectural design and step-by-step tasks required to create the `coc_silver.wars` table in Dataform.

---

## 1. System Context & Grounding

The `coc_silver.wars` table will be built inside the existing Dataform workflow under the `coc_silver` schema. The model will reference the bronze source table `coc_current_war` declared in `definitions/sources.js`. 
To ensure consistency across the project's data warehouse, the table structure, partition lookbacks, and metadata tags are aligned with existing silver models (such as `definitions/clan_members.sqlx` and `definitions/coc_member_hero.sqlx`).

---

## 2. Requirements (EARS Notation)

*   **R1 (Incremental Model Type)**: The system MUST define a Dataform model configured with `type: "incremental"` to support incremental merge runs.
*   **R2 (Target Location)**: The system MUST output the table to the `coc_silver` schema with the filename `definitions/wars.sqlx`.
*   **R3 (Partitioning & Clustering)**: The system MUST partition the table daily on `extracted_date` and cluster it by `["extracted_date", "ptag", "state", "teamSize"]`.
*   **R4 (Granularity)**: The system MUST project records at the **attack level** by unnesting and unioning attacks made by both `clan` members and `opponent` members.
*   **R5 (Ignored Fields)**: The system MUST ignore the `bestOpponentAttack` field during member attack unnesting.
*   **R6 (Stage 1 Deduplication)**: The system MUST use a Common Table Expression (CTE) to select the latest war state payload of the day for each war (grouped by clan tag and opponent tag) before unnesting attacks.
*   **R7 (Stage 2 Deduplication)**: The system MUST apply a `QUALIFY` clause at the end of the query to filter out duplicate unnested attacks on the same day for a player/defender pair (`ptag`/`defender_tag`).
*   **R8 (Constraints & Unique Keys)**: The system MUST enforce a unique composite key constraint using `["extracted_date", "ptag", "defender_tag"]` for merge operations.
*   **R9 (Validation Contract)**: The system MUST configure Dataform assertions for `uniqueKey` and `nonNull` on the columns `["extracted_date", "ptag", "defender_tag"]`.
*   **R10 (Data Governance & FinOps)**: The system MUST include complete descriptions for all columns, assign tags (`["silver", "daily"]`), apply BigQuery labels (`environment: "production"`, `domain: "clash-of-clans"`, `layer: "silver"`), and implement a 2-day lookback partition pruning window for incremental updates.

---

## 3. Technical Decisions

### 3.1 Unnesting Mechanism: `CROSS JOIN UNNEST` vs. `LEFT JOIN UNNEST`
- **Decision**: Use implicit `CROSS JOIN UNNEST` (comma syntax) for both member lists and attack lists.
- **Reasoning**: Because the target table granularity is strictly at the **attack level**, any wars without member arrays or members without attack records are excluded. An inner unnest avoids generating rows with null attacker/defender values, resulting in cleaner downstream ingestion.

### 3.2 Deduplication Strategy
- **Stage 1 (War Level)**: A CTE partitions by `DATE(extracted_at)`, `payload.clan.tag`, and `payload.opponent.tag` to select the latest raw payload snapshot of the day, ensuring that only the most up-to-date state of a war on any given day is processed.
- **Stage 2 (Attack Level)**: A final `QUALIFY` clause partitions by `extracted_date`, `ptag` (attacker tag), and `defender_tag` sorted by `extracted_at DESC` and `attack_order DESC`. This filters out any duplicate records resulting from multiple API snapshots captured on the same calendar day.

---

## 4. Target Schema

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `extracted_at` | `TIMESTAMP` | Timestamp when the war payload was retrieved from Clash of Clans API. |
| `extracted_date` | `DATE` | Partitioning date derived from `extracted_at`. |
| `ptag` | `STRING` | Unique identifier tag of the player performing the attack. |
| `defender_tag` | `STRING` | Unique identifier tag of the player being defended. |
| `state` | `STRING` | The current state of the war (e.g., `preparation`, `inWar`, `warEnded`). |
| `teamSize` | `INT64` | The size of the teams in the war (e.g., 10, 15, 20). |
| `war_clan_tag` | `STRING` | Tag of the home clan. |
| `war_opponent_tag` | `STRING` | Tag of the opponent clan. |
| `member_tag` | `STRING` | Tag of the member who performed the attack (aligns with `ptag`). |
| `member_name` | `STRING` | In-game name of the member who performed the attack. |
| `member_type` | `STRING` | Role of the member's clan in the war (`clan` or `opponent`). |
| `stars` | `INT64` | Number of stars scored in the attack (0-3). |
| `destruction_percentage` | `INT64` | Destruction percentage achieved in the attack (0-100). |
| `attack_order` | `INT64` | Chronological order of the attack in the war. |
| `duration` | `INT64` | Duration of the attack in seconds. |

---

## 5. SQLX Template Design (`definitions/wars.sqlx`)

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
    duration: "Duration of the attack in seconds."
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
    SAFE_CAST(JSON_VALUE(attack.duration) AS INT64) AS duration
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
    SAFE_CAST(JSON_VALUE(attack.duration) AS INT64) AS duration
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
  duration
FROM
  unioned_attacks
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY extracted_date, ptag, defender_tag
  ORDER BY extracted_at DESC, attack_order DESC
) = 1
```

---

## 6. Implementation Tasks

*   [x] **T1**: Create the file `definitions/wars.sqlx` with the config block containing target schema (`coc_silver`), model type (`incremental`), key constraints (`uniqueKey`), assertions (`uniqueKey` and `nonNull`), and metadata tags/labels.
*   [x] **T2**: Implement the `latest_war_payloads` CTE to handle Stage 1 deduplication, including the 2-day lookback for FinOps incremental execution.
*   [x] **T3**: Add the `clan_attacks` and `opponent_attacks` subqueries to unnest player attack records from the JSON payload arrays, excluding the `bestOpponentAttack` field.
*   [x] **T4**: Implement the unioning of both CTEs and the Stage 2 deduplication using `QUALIFY ROW_NUMBER()`.
*   [x] **T5**: Compile the Dataform project using `dataform compile` to verify there are no compilation errors or missing references.
*   [x] **T6**: Run a dry run to verify BigQuery compatibility and permissions using `dataform run --actions wars --dry-run`.
*   [x] **T7**: Perform the initial model execution and verify the created assertions.
