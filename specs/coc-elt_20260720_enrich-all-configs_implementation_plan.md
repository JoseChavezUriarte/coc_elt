---
title: "Enrich All Definitions Configs Implementation Plan"
project_id: "coc-elt"
nyutu_uuid: "d91483f0-eefc-430d-b19b-473d9132941e"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260720_enrich-all-configs_implementation_plan.md"
---

# Implementation Plan - Enrich Config of All Definitions SQLX Files

This plan outlines the design and step-by-step implementation for enriching the configuration blocks of all remaining SQLX files in `definitions/` with descriptions, tags, and BigQuery labels.

---

## 1. System Grounding & Context
- **Target Files**:
  - `definitions/clan_members.sqlx`
  - `definitions/coc_member_achievements.sqlx`
  - `definitions/coc_member_hero.sqlx`
  - `definitions/coc_member_heroEquips.sqlx`
  - `definitions/coc_member_spells.sqlx`
- **Design Pattern**: Data Governance, Orchestration tags, and FinOps labels applied directly in the SQLX `config` block.

---

## 2. Requirements (EARS Notation)
- **R1**: When a `.sqlx` file is updated, the `config` block shall include a comprehensive table `description`.
- **R2**: When a `.sqlx` file is updated, the `config` block shall specify a `tags` array containing `"silver"` and `"daily"`.
- **R3**: When a `.sqlx` file is updated, the `bigquery` configuration block shall specify a `labels` object containing `environment: "production"`, `domain: "clash-of-clans"`, and `layer: "silver"`.
- **R4**: When a `.sqlx` file is updated, the `config` block shall specify a `columns` object detailing descriptions for every projected column in the final SELECT block.
- **R5**: The config updates shall not modify any type, schema, uniqueKey, partitionBy, clusterBy, updatePartitionFilter, assertions, or SQL logic.

---

## 3. SQLX Configuration Templates

### 3.1 `definitions/clan_members.sqlx`
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag"],
  description: "Denormalized and deduplicated silver table containing clan member summary profiles.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "role"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag"],
    nonNull: ["extracted_date", "ptag"]
  },
  columns: {
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player.",
    pname: "Player in-game display name.",
    role: "Role of the member in the clan (e.g. leader, coLeader, admin, member).",
    exp_level: "Player experience level.",
    trophies: "Current trophy count in the main village.",
    war_stars: "Total war stars earned by the player.",
    thl: "Town hall level.",
    bhl: "Builder hall level.",
    capital_contrib: "Total clan capital contributions.",
    btrophies: "Current trophy count in builder base / versus base."
  }
}
```

### 3.2 `definitions/coc_member_achievements.sqlx`
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "achievement_name"],
  description: "Denormalized and deduplicated silver table containing player achievement progress.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "achievement_name", "achievement_village", "achievement_stars"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "achievement_name"],
    nonNull: ["extracted_date", "ptag", "achievement_name"]
  },
  columns: {
    extracted_at: "Timestamp when the player profile raw payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player.",
    achievement_name: "Name of the achievement.",
    achievement_stars: "Number of stars achieved for this achievement.",
    achievement_value: "Current progress value reached for the achievement.",
    achievement_target: "Target value required to complete the current level of achievement.",
    achievement_village: "Village type associated with the achievement (home or builderBase)."
  }
}
```

### 3.3 `definitions/coc_member_hero.sqlx`
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "hero_name"],
  description: "Denormalized and deduplicated silver table containing player hero levels.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "hero_village", "hero_name", "hero_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "hero_name"],
    nonNull: ["extracted_date", "ptag", "hero_name"]
  },
  columns: {
    extracted_at: "Timestamp when the player profile raw payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player.",
    hero_name: "Name of the hero (e.g. Barbarian King, Archer Queen).",
    hero_level: "Current level of the hero upgraded by the player.",
    hero_max_level: "Maximum possible level for the hero.",
    hero_village: "Village where the hero is active (home or builderBase)."
  }
}
```

### 3.4 `definitions/coc_member_heroEquips.sqlx`
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "equipment_name"],
  description: "Denormalized and deduplicated silver table containing player hero equipment statistics.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "equipment_village", "equipment_name", "equipment_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "equipment_name"],
    nonNull: ["extracted_date", "ptag", "equipment_name"]
  },
  columns: {
    extracted_at: "Timestamp when the player profile raw payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player.",
    equipment_name: "Name of the hero equipment (e.g. Giant Gauntlet, Invisibility Vial).",
    equipment_level: "Current level of the hero equipment.",
    equipment_max_level: "Maximum possible level for the hero equipment.",
    equipment_village: "Village where the hero equipment is active (home or builderBase)."
  }
}
```

### 3.5 `definitions/coc_member_spells.sqlx`
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag", "spell_name"],
  description: "Denormalized and deduplicated silver table containing player spell statistics.",
  tags: ["silver", "daily"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "spell_village", "spell_name", "spell_level"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
    labels: {
      environment: "production",
      domain: "clash-of-clans",
      layer: "silver"
    }
  },
  assertions: {
    uniqueKey: ["extracted_date", "ptag", "spell_name"],
    nonNull: ["extracted_date", "ptag", "spell_name"]
  },
  columns: {
    extracted_at: "Timestamp when the player profile raw payload was retrieved from Clash of Clans API.",
    extracted_date: "Partitioning date derived from extracted_at.",
    ptag: "Unique identifier tag of the player.",
    spell_name: "Name of the spell (e.g. Lightning Spell, Healing Spell).",
    spell_level: "Current level of the spell upgraded by the player.",
    spell_max_level: "Maximum possible level for the spell.",
    spell_village: "Village where the spell is active (home or builderBase)."
  }
}
```

---

## 4. Implementation Tasks

- [x] **T1: Apply Configuration Modifications for clan_members.sqlx**
- [x] **T2: Apply Configuration Modifications for coc_member_achievements.sqlx**
- [x] **T3: Apply Configuration Modifications for coc_member_hero.sqlx**
- [x] **T4: Apply Configuration Modifications for coc_member_heroEquips.sqlx**
- [x] **T5: Apply Configuration Modifications for coc_member_spells.sqlx**
- [x] **T6: Validate Syntax and Compilation**
  - Run `pnpm exec dataform compile` to ensure there are no syntax errors or compilation issues.
