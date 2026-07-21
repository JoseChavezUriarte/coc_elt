---
title: "Optimize BigQuery Clustering Keys"
project_id: "coc-elt"
nyutu_uuid: "734317f5-6945-4cfd-bd26-17077e9e8e30"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260721_optimize-clustering-keys_implementation_plan.md"
---

# Implementation Plan - Optimize BigQuery Clustering Keys

This plan outlines the changes required to optimize BigQuery clustering configuration in `definitions/clan_description.sqlx` and `definitions/wars.sqlx` by removing the redundant `extracted_date` partitioning column from the clustering keys.

---

## 1. System Context & Rationale

Both `clan_description` and `wars` tables are partitioned by `extracted_date`. BigQuery automatically organizes data into partition blocks based on this column. 
Specifying `extracted_date` as the first element in the `clusterBy` array is redundant and can hinder the efficiency of clustering on high-cardinality fields like `tag` or `ptag`. Removing `extracted_date` aligns these tables with best practices and existing patterns (e.g., in `definitions/clan_members.sqlx`).

---

## 2. Requirements (EARS Notation)

- **R1 (Clustering Optimization - Clan Description)**: When the Dataform compilation runs, the table `definitions/clan_description.sqlx` **shall** be configured to cluster only by `["tag"]`.
- **R2 (Clustering Optimization - Wars)**: When the Dataform compilation runs, the table `definitions/wars.sqlx` **shall** be configured to cluster by `["ptag", "state", "teamSize"]`.
- **R3 (Configuration Preservation)**: Where the clustering configurations are modified, all other table configurations (such as `partitionBy`, `uniqueKey`, `updatePartitionFilter`, `assertions`, `labels`, and `columns` metadata) and queries **shall** remain unchanged.
- **R4 (Local Validation)**: When the codebase is modified, the Dataform project **shall** compile successfully locally with no validation or configuration errors.

---

## 3. Proposed Code Changes

### Target 1: `definitions/clan_description.sqlx`

Modify the `clusterBy` option inside the `bigquery` configuration block:

```diff
--- definitions/clan_description.sqlx
+++ definitions/clan_description.sqlx
@@ -7,5 +7,5 @@
   bigquery: {
     partitionBy: "extracted_date",
-    clusterBy: ["extracted_date", "tag"],
+    clusterBy: ["tag"],
     updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
```

### Target 2: `definitions/wars.sqlx`

Modify the `clusterBy` option inside the `bigquery` configuration block:

```diff
--- definitions/wars.sqlx
+++ definitions/wars.sqlx
@@ -7,5 +7,5 @@
   bigquery: {
     partitionBy: "extracted_date",
-    clusterBy: ["extracted_date", "ptag", "state", "teamSize"],
+    clusterBy: ["ptag", "state", "teamSize"],
     updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
```

---

## 4. Implementation & Verification Tasks

- [x] **T1: Optimize `clan_description.sqlx`**: Update `definitions/clan_description.sqlx` to change `clusterBy` from `["extracted_date", "tag"]` to `["tag"]`.
- [x] **T2: Optimize `wars.sqlx`**: Update `definitions/wars.sqlx` to change `clusterBy` from `["extracted_date", "ptag", "state", "teamSize"]` to `["ptag", "state", "teamSize"]`.
- [x] **T3: Validate Compilation**: Run `pnpm exec dataform compile` to verify successful compilation.
