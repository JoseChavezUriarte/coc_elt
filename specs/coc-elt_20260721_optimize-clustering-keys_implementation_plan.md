---
title: "Optimize BigQuery Clustering Keys"
project_id: "coc-elt"
nyutu_uuid: "07649d8d-278c-4222-8c0a-dfbb28f4f5b2"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "bigquery"
  - "silver-layer"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260721_optimize-clustering-keys_implementation_plan.md"
---

# Implementation Plan - Optimize BigQuery Clustering Keys (Revised with Production Push)

This plan outlines the changes required to optimize BigQuery clustering configuration in `definitions/clan_description.sqlx` and `definitions/wars.sqlx` by setting the requested clustering keys, pushing to production, dropping the active BigQuery tables, and rebuilding them via the GCP Workflow.

---

## 1. System Context & Rationale

Both `clan_description` and `wars` tables are partitioned by `extracted_date`. BigQuery automatically organizes data into partition blocks based on this column. 
Specifying `extracted_date` as the first element in the `clusterBy` array is redundant and has been removed. We will set custom clustering keys based on the analytical requirements of the dashboards:
- `wars`: clustered on `["ptag", "state", "mapPosition", "townhallLevel"]`.
- `clan_description`: clustered on `["clanLevel", "members", "warWins", "warLosses"]`.

Since BigQuery does not support modifying the clustering structure of an existing table in-place, the target tables must be dropped and recreated in production to apply the updated clustering schemas.

---

## 2. Requirements (EARS Notation)

- **R1 (Clustering Optimization - Clan Description)**: When the Dataform compilation runs, the table `definitions/clan_description.sqlx` **shall** be configured to cluster by `["clanLevel", "members", "warWins", "warLosses"]`.
- **R2 (Clustering Optimization - Wars)**: When the Dataform compilation runs, the table `definitions/wars.sqlx` **shall** be configured to cluster by `["ptag", "state", "mapPosition", "townhallLevel"]`.
- **R3 (Production Push)**: The developer **shall** push the changes to the production repository's `main` branch to trigger CI/CD updates.
- **R4 (BigQuery Table Drop)**: To apply the new clustering keys, the developer **shall** delete the existing physical tables `coc_silver.wars` and `coc_silver.clan_description` before executing the pipeline.
- **R5 (Pipeline Rebuild & Validation)**: The developer **shall** execute the GCP Workflow `coc-elt-workflow` to rebuild and backfill both tables, and query the BigQuery metadata to verify clustering properties.

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
-    clusterBy: ["tag"],
+    clusterBy: ["clanLevel", "members", "warWins", "warLosses"],
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
-    clusterBy: ["ptag", "state", "teamSize"],
+    clusterBy: ["ptag", "state", "mapPosition", "townhallLevel"],
     updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)",
```

---

## 4. Implementation Tasks

- [x] **T1: Optimize SQLX Files**: Update `definitions/clan_description.sqlx` and `definitions/wars.sqlx` clustering keys as specified.
- [x] **T2: Validate Compilation**: Run `pnpm exec dataform compile` to verify successful compilation locally.
- [x] **T3: Push Changes to Main**: Stage, commit, and push the changes to `origin/main`.
- [x] **T4: Delete BigQuery Tables**: Delete the existing physical tables `coc_silver.wars` and `coc_silver.clan_description` in BigQuery.
- [x] **T5: Execute Workflow**: Run the GCP Workflow `coc-elt-workflow` to rebuild the tables and perform the backfill.
- [x] **T6: Verify Clustering Metadata**: Query BQ schemas to verify clustering configuration is successfully updated.
