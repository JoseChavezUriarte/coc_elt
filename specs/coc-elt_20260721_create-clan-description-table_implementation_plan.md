---
title: "Create clan_description Table in coc_silver"
project_id: "coc-elt"
nyutu_uuid: "53ad165d-cbdf-462a-b613-aacf918bb905"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260721_create-clan-description-table_implementation_plan.md"
---

# Implementation Plan: `coc_silver.clan_description`

This plan outlines the architecture, requirements, technical design, and sequential implementation tasks to create the `coc_silver.clan_description` silver table in Dataform.

---

## 1. System Context & Codebase Grounding
- **Source Table**: `coc_bronze.coc_clan` (as declared in [sources.js](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/sources.js)).
- **Target Table**: `coc_silver.clan_description` (to be created at `definitions/clan_description.sqlx`).
- **Pattern Match**: The configuration, incremental update filter, deduplication pattern, and data governance labels match the design of `definitions/clan_members.sqlx`.

---

## 2. File Actions
- **New File**: Create `definitions/clan_description.sqlx` containing the Dataform SQLX definition.
- **Modifications**: None.

---

## 3. Requirements (EARS Notation)
- **R1 (Partitioning & Clustering)**: The `clan_description` table **shall** be partitioned by `extracted_date` and clustered by `["extracted_date", "tag"]`.
- **R2 (Incremental Filter)**: When executing Dataform in incremental mode, the compilation pipeline **shall** filter source records using `extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))` and update partition ranges using `extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)`.
- **R3 (Array Exclusion)**: While parsing the source payload, the model **shall** ignore the nested arrays/objects `clanCapital` and `memberList`.
- **R4 (Daily Deduplication)**: If duplicate payloads for a clan tag occur on the same `extracted_date`, the query **shall** select only the latest payload of that day based on `extracted_at DESC`.
- **R5 (Numeric & Boolean Casts)**: The model **shall** apply `SAFE_CAST` to numeric and boolean columns to prevent execution failures on invalid formats.

---

## 4. Technical Decisions & Trade-Offs

### BigQuery Config Decisions
- **Partitioning Strategy**: Partitioning by `extracted_date` (derived from `DATE(extracted_at)`) allows for cost-efficient query scans on daily granular boundaries.
- **Clustering Strategy**: Clustering on `["extracted_date", "tag"]` is optimal for queries filtered or grouped by specific clan tags and dates.
- **Deduplication Strategy**: We utilize a `ROW_NUMBER() OVER (PARTITION BY extracted_date, tag ORDER BY extracted_at DESC)` window function in a CTE to isolate the last status of the clan for each day, matching the project's strategy for capturing daily historical snapshots.

---

## 5. SQLX Code Template

Below is the proposed contents for `definitions/clan_description.sqlx`:

```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "tag"],
  description: "Deduplicated and structured daily snapshots of clan profile descriptions and metadata.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["extracted_date", "tag"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "tag"],
    nonNull: ["extracted_date", "tag"]
  },
  columns: {
    extracted_at: "Timestamp when the clan profile raw payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    tag: "Unique identifier tag of the clan.",
    name: "Name of the clan.",
    type: "Type of the clan (e.g. inviteOnly, closed, open).",
    description: "Description of the clan.",
    clanLevel: "Level of the clan.",
    clanPoints: "Total clan points in the main village.",
    clanBuilderBasePoints: "Total clan points in the builder base.",
    clanCapitalPoints: "Total clan points in the clan capital.",
    capitalLeague: "Name of the capital league of the clan.",
    chatLanguage: "Language used for clan chat.",
    location: "Location of the clan.",
    warLeague: "Name of the war league of the clan.",
    isFamilyFriendly: "Whether the clan is family friendly.",
    isWarLogPublic: "Whether the clan war log is public.",
    members: "Number of members in the clan.",
    requiredBuilderBaseTrophies: "Required builder base trophies to join.",
    requiredTownhallLevel: "Required minimum townhall level to join.",
    requiredTrophies: "Required trophies to join.",
    warFrequency: "War frequency of the clan.",
    warLosses: "Total number of war losses.",
    warTies: "Total number of war ties.",
    warWinStreak: "Current war win streak.",
    warWins: "Total number of war wins."
  }
}

WITH parsed_clans AS (
  SELECT
    extracted_at,
    DATE(extracted_at) AS extracted_date,
    JSON_VALUE(payload.tag) AS tag,
    JSON_VALUE(payload.name) AS name,
    JSON_VALUE(payload.type) AS type,
    JSON_VALUE(payload.description) AS description,
    SAFE_CAST(JSON_VALUE(payload.clanLevel) AS INT64) AS clanLevel,
    SAFE_CAST(JSON_VALUE(payload.clanPoints) AS INT64) AS clanPoints,
    SAFE_CAST(JSON_VALUE(payload.clanBuilderBasePoints) AS INT64) AS clanBuilderBasePoints,
    SAFE_CAST(JSON_VALUE(payload.clanCapitalPoints) AS INT64) AS clanCapitalPoints,
    JSON_VALUE(payload.capitalLeague.name) AS capitalLeague,
    JSON_VALUE(payload.chatLanguage.name) AS chatLanguage,
    JSON_VALUE(payload.location.name) AS location,
    JSON_VALUE(payload.warLeague.name) AS warLeague,
    SAFE_CAST(JSON_VALUE(payload.isFamilyFriendly) AS BOOL) AS isFamilyFriendly,
    SAFE_CAST(JSON_VALUE(payload.isWarLogPublic) AS BOOL) AS isWarLogPublic,
    SAFE_CAST(JSON_VALUE(payload.members) AS INT64) AS members,
    SAFE_CAST(JSON_VALUE(payload.requiredBuilderBaseTrophies) AS INT64) AS requiredBuilderBaseTrophies,
    SAFE_CAST(JSON_VALUE(payload.requiredTownhallLevel) AS INT64) AS requiredTownhallLevel,
    SAFE_CAST(JSON_VALUE(payload.requiredTrophies) AS INT64) AS requiredTrophies,
    JSON_VALUE(payload.warFrequency) AS warFrequency,
    SAFE_CAST(JSON_VALUE(payload.warLosses) AS INT64) AS warLosses,
    SAFE_CAST(JSON_VALUE(payload.warTies) AS INT64) AS warTies,
    SAFE_CAST(JSON_VALUE(payload.warWinStreak) AS INT64) AS warWinStreak,
    SAFE_CAST(JSON_VALUE(payload.warWins) AS INT64) AS warWins
  FROM
    ${ref("coc_clan")}
  ${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
),

ranked_clans AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, tag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_clans
)

SELECT
  extracted_at,
  extracted_date,
  tag,
  name,
  type,
  description,
  clanLevel,
  clanPoints,
  clanBuilderBasePoints,
  clanCapitalPoints,
  capitalLeague,
  chatLanguage,
  location,
  warLeague,
  isFamilyFriendly,
  isWarLogPublic,
  members,
  requiredBuilderBaseTrophies,
  requiredTownhallLevel,
  requiredTrophies,
  warFrequency,
  warLosses,
  warTies,
  warWinStreak,
  warWins
FROM
  ranked_clans
WHERE
  row_num = 1
```

---

## 6. Implementation & Verification Steps
- [x] **T1: Create SQLX File**: Write the above SQLX structure to `definitions/clan_description.sqlx`.
- [x] **T2: Run Dataform Compile**: Execute `dataform compile` to ensure syntax validness, dependency resolution, and accurate generation of assertions.
- [x] **T3: Local Dry Run**: Execute dry run locally or verify compilation.
