---
title: "Dual-Asset Clan Member Activity Architecture in Dataform (Revised)"
project_id: "coc-elt"
nyutu_uuid: "76124b84-88ae-49c1-8112-84641c4fb37d"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "bigquery"
  - "gold-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260802_clan-member-activity-tables_implementation_plan.md"
---

## 1. System Context & Codebase Grounding
- The `coc_elt` pipeline tracks granular silver layer upgrades across 5 specialized tables:
  1. `clan_member_upgrades`
  2. `coc_member_hero_upgrades`
  3. `coc_member_spells_upgrades`
  4. `coc_member_troops_upgrades`
  5. `coc_member_heroEquips_upgrades`
- Business Requirement: Materialize member activity aggregations into the `coc_gold` dataset using a decoupled dual-asset model:
  - **Historical Asset (`clan_member_activity_historical.sqlx`)**: Incremental table partitioned by day (`generated_at`).
  - **Hot Asset (`clan_member_activity_hot.sqlx`)**: Daily refreshed table selecting the active execution partition directly.

## 2. Technical Directives & Architectural Corrections

### Directive 1: Strict Dataset Enforcement
Both assets MUST explicitly set `schema: "coc_gold"` in their `config` blocks. No default or variable schema fallbacks are permitted.

### Directive 2: Temporal Idempotency via Deterministic JS Timestamp
All occurrences of `CURRENT_DATE()` and `CURRENT_TIMESTAMP()` are REMOVED.
- Source filter in `clan_member_activity_historical.sqlx`:
  ```sql
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}
  ```
- Partition generation timestamp:
  ```sql
  TIMESTAMP('${execution_ts}') AS generated_at
  ```

### Directive 3: Direct Partition Pruning in Hot Asset (FinOps Optimization)
Subquery scalar evaluation (`(SELECT MAX(generated_at)...)`) is REMOVED to eliminate BigQuery query planner pre-evaluation delays and compute slot double-billing.
- The `execution_ts` JS variable is declared in `clan_member_activity_hot.sqlx`.
- Partition filter uses literal equality:
  ```sql
  WHERE generated_at = TIMESTAMP('${execution_ts}')
  ```

### Directive 4: Upstream Freshness Assumption & Quality Guardrails
**Technical Note on Upstream Freshness**:
Decoupling the execution timestamp (`execution_ts`) from dynamic BigQuery `MAX(extracted_date)` scans assumes that upstream Dataform pipelines enforce **Data Freshness Assertions** on the `coc_silver` layer. If upstream ingestion stalls, executing `clan_member_activity_historical` with a newer `execution_ts` will create a new partition carrying 0 activity for that day. Dataform assertions on silver tables (`uniqueKey`, `nonNull`, `rowConditions`) act as the circuit breaker preventing stale runs.

---

## 3. Requirements (EARS Notation)

### 3.1 Historical Asset (`definitions/clan_member_activity_historical.sqlx`)
- **R1 (Materialization & Dataset)**: The asset MUST be configured with `type: "incremental"` and `schema: "coc_gold"`.
- **R2 (Partitioning & Clustering)**: `partitionBy: "DATE(generated_at)"` (DAY partition on TIMESTAMP) and `clusterBy: ["ptag", "activity"]`.
- **R3 (Temporal Idempotency)**: The system MUST derive `generated_at` and `extracted_date` filters deterministically from `DATE('${execution_ts}')` / `TIMESTAMP('${execution_ts}')`.
- **R4 (Dependency Graph)**: The system MUST reference source tables using `${ref("clan_member_upgrades")}`, `${ref("coc_member_hero_upgrades")}`, `${ref("coc_member_spells_upgrades")}`, `${ref("coc_member_troops_upgrades")}`, and `${ref("coc_member_heroEquips_upgrades")}`.

### 3.2 Hot Asset (`definitions/clan_member_activity_hot.sqlx`)
- **R5 (Materialization & Dataset)**: The asset MUST be configured with `type: "table"` and `schema: "coc_gold"`.
- **R6 (Direct Partition Filtering)**: The asset MUST filter partition scans using literal timestamp equality `WHERE generated_at = TIMESTAMP('${execution_ts}')` to guarantee constant-time partition pruning.

---

## 4. SQLX Code Design Templates

### Template 1: `definitions/clan_member_activity_historical.sqlx`

```sqlx
config {
  type: "incremental",
  schema: "coc_gold",
  uniqueKey: ["generated_at", "ptag"],
  description: "Historical daily partition snapshot tracking member activity scores calculated across all upgrade dimensions.",
  tags: ["gold", "daily", "activity"],
  bigquery: {
    partitionBy: "DATE(generated_at)",
    clusterBy: ["ptag", "activity"],
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "gold"
    }
  },
  assertions: {
    uniqueKey: ["generated_at", "ptag"],
    nonNull: ["generated_at", "ptag", "activity"]
  },
  columns: {
    generated_at: "Deterministic execution timestamp when this snapshot partition was generated.",
    ptag: "Unique player tag identifier.",
    wars_active: "Indicator (1/0) if player participated in war stars progression.",
    capital_active: "Indicator (1/0) if player contributed to clan capital.",
    th_active: "Indicator (1/0) if player upgraded town hall.",
    upgrade_hero: "Indicator (1/0) if player upgraded any hero.",
    upgrade_spell: "Indicator (1/0) if player upgraded any spell.",
    upgrade_troop: "Indicator (1/0) if player upgraded any troop.",
    upgrade_heroEquip: "Indicator (1/0) if player upgraded any hero equipment.",
    activity: "Aggregated activity score (sum of all 7 activity indicators, range 0-7)."
  }
}

js {
  const execution_ts = dataform.projectConfig.vars.execution_timestamp || "2026-08-02T12:00:00Z";
}

WITH unified_metrics AS (
  SELECT 
    ptag,
    CASE WHEN war_stars_var > 0 THEN 1 ELSE 0 END AS wars_active,
    CASE WHEN capital_contrib_var > 0 THEN 1 ELSE 0 END AS capital_active,
    CASE WHEN thl_var > 0 THEN 1 ELSE 0 END AS th_active,
    0 AS upgrade_hero,
    0 AS upgrade_spell,
    0 AS upgrade_troop,
    0 AS upgrade_heroEquip
  FROM ${ref("clan_member_upgrades")}
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}

  UNION ALL

  SELECT 
    ptag, 0, 0, 0, 
    CASE WHEN level_var > 0 THEN 1 ELSE 0 END, 
    0, 0, 0
  FROM ${ref("coc_member_hero_upgrades")}
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}

  UNION ALL

  SELECT 
    ptag, 0, 0, 0, 0, 
    CASE WHEN level_var > 0 THEN 1 ELSE 0 END, 
    0, 0
  FROM ${ref("coc_member_spells_upgrades")}
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}

  UNION ALL

  SELECT 
    ptag, 0, 0, 0, 0, 0, 
    CASE WHEN level_var > 0 THEN 1 ELSE 0 END, 
    0
  FROM ${ref("coc_member_troops_upgrades")}
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}

  UNION ALL

  SELECT 
    ptag, 0, 0, 0, 0, 0, 0, 
    CASE WHEN level_var > 0 THEN 1 ELSE 0 END
  FROM ${ref("coc_member_heroEquips_upgrades")}
  ${when(incremental(), `WHERE extracted_date >= DATE_SUB(DATE('${execution_ts}'), INTERVAL 7 DAY)`)}
),

active_matrix AS (
  SELECT 
    TIMESTAMP('${execution_ts}') AS generated_at,
    ptag,
    MAX(wars_active) AS wars_active,
    MAX(capital_active) AS capital_active,
    MAX(th_active) AS th_active,
    MAX(upgrade_hero) AS upgrade_hero,
    MAX(upgrade_spell) AS upgrade_spell,
    MAX(upgrade_troop) AS upgrade_troop,
    MAX(upgrade_heroEquip) AS upgrade_heroEquip
  FROM unified_metrics
  GROUP BY ptag
)

SELECT
  generated_at,
  ptag,
  wars_active,
  capital_active,
  th_active,
  upgrade_hero,
  upgrade_spell,
  upgrade_troop,
  upgrade_heroEquip,
  (wars_active + capital_active + th_active + upgrade_hero + upgrade_spell + upgrade_troop + upgrade_heroEquip) AS activity
FROM active_matrix
```

---

### Template 2: `definitions/clan_member_activity_hot.sqlx`

```sqlx
config {
  type: "table",
  schema: "coc_gold",
  description: "Hot asset serving current active member snapshot by querying latest partition of clan_member_activity_historical using literal execution timestamp.",
  tags: ["gold", "daily", "activity", "hot"],
  bigquery: {
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "gold"
    }
  },
  assertions: {
    uniqueKey: ["ptag"],
    nonNull: ["generated_at", "ptag", "activity"]
  },
  columns: {
    generated_at: "Snapshot generation timestamp of the current active partition.",
    ptag: "Unique player tag identifier.",
    wars_active: "Indicator (1/0) if player participated in war stars progression.",
    capital_active: "Indicator (1/0) if player contributed to clan capital.",
    th_active: "Indicator (1/0) if player upgraded town hall.",
    upgrade_hero: "Indicator (1/0) if player upgraded any hero.",
    upgrade_spell: "Indicator (1/0) if player upgraded any spell.",
    upgrade_troop: "Indicator (1/0) if player upgraded any troop.",
    upgrade_heroEquip: "Indicator (1/0) if player upgraded any hero equipment.",
    activity: "Aggregated activity score (0-7)."
  }
}

js {
  const execution_ts = dataform.projectConfig.vars.execution_timestamp || "2026-08-02T12:00:00Z";
}

SELECT
  generated_at,
  ptag,
  wars_active,
  capital_active,
  th_active,
  upgrade_hero,
  upgrade_spell,
  upgrade_troop,
  upgrade_heroEquip,
  activity
FROM
  ${ref("clan_member_activity_historical")}
WHERE
  generated_at = TIMESTAMP('${execution_ts}')
```

---

## 5. Implementation Tasks (Pending Explicit User Approval)

- [ ] **T1**: Create `definitions/clan_member_activity_historical.sqlx` in `coc_gold`.
- [ ] **T2**: Create `definitions/clan_member_activity_hot.sqlx` in `coc_gold`.
- [ ] **T3**: Verify local Dataform compilation (`pnpm dataform compile`).
- [ ] **T4**: Create walkthrough spec [`specs/coc-elt_20260802_clan-member-activity-tables_walkthrough.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260802_clan-member-activity-tables_walkthrough.md).
