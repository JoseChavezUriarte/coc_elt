---
title: "Create clan_weekly_performance Table in coc_gold"
project_id: "coc-elt"
nyutu_uuid: "f2a219be-ca01-46dc-8c11-57d4ac14acf6"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "gold-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260728_create-clan-weekly-performance-table_implementation_plan.md"
---

## 1. System Context & Codebase Grounding
- The project `coc_elt` leverages Dataform to model BigQuery data.
- The source table is `clan_description` (configured via `clan_description.sqlx`).
- The target dataset/schema is `coc_gold`.
- The new table `clan_weekly_performance` will aggregate daily snapshots into weekly cohorts to summarize weekly clan performance.

## 2. File Actions
- **Create File:** `definitions/clan_weekly_performance.sqlx` under `/home/scheveningen/documents/proyectos/coc_elt`
  - Purpose: Define the `clan_weekly_performance` incremental table in Dataform.

## 3. Requirements (EARS Notation)
- **R1:** The system MUST configure the table in the `coc_gold` schema as an incremental type with `uniqueKey` set to `["week_start_date"]`.
- **R2:** The system MUST reference the source data using `${ref("clan_description")}`.
- **R3:** WHEN running incrementally, the system MUST filter source data to dates since the start of the previous week (`extracted_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY), WEEK(MONDAY))`).
- **R4:** WHEN NOT running incrementally, the system MUST NOT apply any date limit, loading the entire historical dataset from `clan_description`.
- **R5:** The system MUST add assertions for uniqueness and non-nullability on `week_start_date`.

## 4. Technical Decisions & Trade-Offs
- **Weekly Cohort Start:** Week definition starts on Monday (`WEEK(MONDAY)`) for alignment with common business reporting.
- **Incremental Interval:** A 7-day interval truncated to Monday ensures that daily runs dynamically recalculate the current incomplete week while simultaneously guaranteeing completeness for the immediately preceding week (i.e. late arrivals or boundary conditions).
- **Partitioning & Clustering:** Removed due to low data volume, optimizing simplicity over unnecessary BigQuery storage configuration overhead.
- **Unique Key constraints:** `week_start_date` serves as the idempotent identifier for a weekly snapshot, allowing Dataform's merge functionality to cleanly upsert data.

## 5. SQLX Code Template

```javascript
config {
    type: "incremental",
    schema: "coc_gold",
    uniqueKey: ["week_start_date"],
    description: "Weekly performance aggregation of clan stats based on daily snapshots.",
    tags: ["gold", "daily"],
    bigquery: {
        labels: {
            environment: "production",
            domain: "clash-of-clans",
            layer: "gold"
        }
    },
    assertions: {
        uniqueKey: ["week_start_date"],
        nonNull: ["week_start_date"]
    },
    columns: {
        week_start_date: "The start date of the week (the Monday of that week).",
        week_num: "The week number of the year (starting Monday).",
        year: "The year of the weekly cohort.",
        last_date: "The latest snapshot date within this week.",
        first_date: "The earliest snapshot date within this week.",
        regs: "Number of snapshot records aggregated in this week.",
        w_ClanPoints: "Clan points recorded on the last_date of the week.",
        w_clanBuilderBasePoints: "Clan builder base points on the last_date.",
        w_clanCapitalPoints: "Clan capital points on the last_date.",
        w_warWins: "Total war wins on the last_date.",
        w_warTies: "Total war ties on the last_date.",
        w_warLosses: "Total war losses on the last_date.",
        w_members: "Number of members in the clan on the last_date."
    }
}

WITH cohortes_semanales AS (
    SELECT
        DATE_TRUNC(extracted_date, WEEK(MONDAY)) AS week_start_date,
        MAX(extracted_date) AS last_date,
        MIN(extracted_date) AS first_date,
        COUNT(*) AS regs,
        ARRAY_AGG(
            STRUCT(
                clanPoints AS w_ClanPoints,
                clanBuilderBasePoints AS w_clanBuilderBasePoints,
                clanCapitalPoints AS w_clanCapitalPoints,
                warWins AS w_warWins,
                warTies AS w_warTies,
                warLosses AS w_warLosses,
                members AS w_members
            ) 
            ORDER BY extracted_date DESC 
            LIMIT 1
        )[OFFSET(0)] AS latest_stats
    FROM ${ref("clan_description")}
    ${when(incremental(), 
        `WHERE extracted_date >= DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY), WEEK(MONDAY))`
    )}
    GROUP BY 1
)
SELECT
    week_start_date,
    EXTRACT(WEEK(MONDAY) FROM week_start_date) AS week_num,
    EXTRACT(YEAR FROM week_start_date) AS year,
    last_date,
    first_date,
    regs,
    latest_stats.w_ClanPoints,
    latest_stats.w_clanBuilderBasePoints,
    latest_stats.w_clanCapitalPoints,
    latest_stats.w_warWins,
    latest_stats.w_warTies,
    latest_stats.w_warLosses,
    latest_stats.w_members
FROM cohortes_semanales
```

## 6. Implementation & Verification Steps
- [x] **T1:** Create the SQLX file `definitions/clan_weekly_performance.sqlx` with the provided template.
- [x] **T2:** Verify Dataform compilation locally (`npx dataform compile`).
- [ ] **T3:** Run/schedule Dataform pipeline execution.
