---
title: "Enrich Config of coc_member_troops.sqlx Implementation Plan"
project_id: "coc-elt"
nyutu_uuid: "48474185-3cb9-4423-a381-c06cb8c32c25"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260720_enrich-troops-config_implementation_plan.md"
---

# Implementation Plan - Enrich Config of coc_member_troops.sqlx

This plan outlines the design and step-by-step implementation for enriching the configuration block of `definitions/coc_member_troops.sqlx` with table/column descriptions, tags, and BigQuery labels.

---

## 1. System Grounding & Context
- **Target File**: [definitions/coc_member_troops.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_troops.sqlx)
- **Design Pattern**: Data Governance, Orchestration tags, and FinOps labels applied directly in the SQLX `config` block.

---

## 2. Requirements (EARS Notation)
- **R1 (Table Metadata)**: The `definitions/coc_member_troops.sqlx` configuration block SHALL define a table-level description string matching `"Denormalized and deduplicated silver table containing player troop statistics."`.
- **R2 (Tags)**: The `definitions/coc_member_troops.sqlx` configuration block SHALL specify a `tags` array containing `"silver"` and `"daily"`.
- **R3 (BigQuery Labels)**: The `definitions/coc_member_troops.sqlx` `bigquery` configuration block SHALL specify a `labels` object containing `environment: "production"`, `domain: "clash-of-clans"`, and `layer: "silver"`.
- **R4 (Columns Documentation)**: The `definitions/coc_member_troops.sqlx` configuration block SHALL specify a `columns` object detailing descriptions for every projected column (`extracted_at`, `extracted_date`, `ptag`, `troop_name`, `troop_level`, `troop_max_level`, and `troop_village`).
- **R5 (No regression)**: The enrichment of the config block SHALL NOT modify the table type, schema, uniqueKey, existing bigquery settings (partitionBy, clusterBy, updatePartitionFilter), assertions, or the SQL query itself.

---

## 3. Technical Decisions & Trade-offs
### Decision 1: Placement of Metadata Elements inside `config` block
- **Option A**: Append all metadata to the end of the `config` block.
- **Option B**: Group general table properties (description, tags) near the top, and schema metadata (columns) at the bottom.
- **Selected**: **Option B**.
  - *Pros*: Enhances code readability by placing short global table properties near the header settings, and listing detailed column mappings at the end of the block.
  - *Cons*: Slightly changes config line sequencing but matches standard Dataform best practices.

---

## 4. File Specifications & Templates

### File: [definitions/coc_member_troops.sqlx](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/coc_member_troops.sqlx)

```diff
--- a/definitions/coc_member_troops.sqlx
+++ b/definitions/coc_member_troops.sqlx
@@ -1,14 +1,28 @@
 config {
   type: "incremental",
   schema: "coc_silver",
   uniqueKey: ["extracted_date", "ptag", "troop_name"],
+  description: "Denormalized and deduplicated silver table containing player troop statistics.",
+  tags: ["silver", "daily"],
   bigquery: {
     partitionBy: "extracted_date",
     clusterBy: ["ptag", "troop_village", "troop_name", "troop_level"],
-    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
+    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
+    labels: {
+      environment: "production",
+      domain: "clash-of-clans",
+      layer: "silver"
+    }
   },
   assertions: {
     uniqueKey: ["extracted_date", "ptag", "troop_name"],
     nonNull: ["extracted_date", "ptag", "troop_name"]
-  }
+  },
+  columns: {
+    extracted_at: "Timestamp when the player profile raw payload was retrieved from Clash of Clans API.",
+    extracted_date: "Partitioning date derived from extracted_at.",
+    ptag: "Unique identifier tag of the player.",
+    troop_name: "Name of the troop (e.g. Barbarian, Archer).",
+    troop_level: "Current level of the troop upgraded by the player.",
+    troop_max_level: "Maximum possible level for the troop.",
+    troop_village: "Village where the troop is active (home or builderBase)."
+  }
 }
```

---

## 5. Implementation Tasks

- [x] **T1: Apply Configuration Modifications**
  - Update `definitions/coc_member_troops.sqlx` configuration block with the proposed structure shown in the diff above.
- [x] **T2: Validate Syntax and Compilation**
  - Run `pnpm exec dataform compile` to ensure there are no syntax errors, invalid settings, or compilation issues.
