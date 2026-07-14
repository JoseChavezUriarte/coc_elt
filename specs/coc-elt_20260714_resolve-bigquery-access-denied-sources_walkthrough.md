---
title: "Resolve BigQuery Access Denied in Dataform Sources Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "40c706c4-976b-436c-9a50-b445ece90449"
artifact_type: "Bug Fix Logic"
tags:
  - "dataform"
  - "bigquery"
  - "walkthrough"
source_uri: "specs/coc-elt_20260714_resolve-bigquery-access-denied-sources_walkthrough.md"
---

# Walkthrough: Resolve BigQuery Access Denied in Dataform Sources

This walkthrough documents the modifications made to the Dataform source definitions to resolve the BigQuery access denied error in production by transitioning to implicit database resolution.

## 1. Description of the Issue

In the Dataform setup for the `coc-elt` project, the source definitions inside `definitions/sources.js` were configured with a hardcoded `database` field pointing to `coc-data-analytics-project`:
```javascript
declare({
  database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_clan"
});
```

During execution in production environments (like GCP Workflows), the service account running the Dataform job lacks permission to query `coc-data-analytics-project` directly. Instead, tables reside within the specific runtime environment's data project database (such as `swift-capsule-492817-a7`). Because the `database` property was hardcoded, Dataform ignored any dynamic compile-time or runtime defaults (e.g. `defaultDatabase` overrides) and attempted to query `coc-data-analytics-project` directly, resulting in an `Access Denied` error.

## 2. Configuration Modification

To fix this, we modified `definitions/sources.js` to completely remove the `database` configuration property from all declare blocks. This allows Dataform to fallback to the compilation environment's `defaultDatabase` (either configured in `dataform.json` for local/default compilation or overridden dynamically at runtime).

The diff of the changes in `definitions/sources.js` is:
```diff
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_clan"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_members"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_current_war"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_capital_raids"
});
```

By removing the explicit database declarations, the compile step resolves the datasets relative to whichever database/project is passed as the default compilation project.

## 3. Verification

### 3.1 Dataform Compilation
Run `pnpm exec dataform compile` at the project root:
```bash
pnpm exec dataform compile
```

Output:
```text
Compiling...

Compiled 3 action(s).
1 dataset(s):
  coc_silver.clan_members [incremental]
2 assertion(s):
  coc_assertions.coc_silver_clan_members_assertions_uniqueKey_0
  coc_assertions.coc_silver_clan_members_assertions_rowConditions
```

The compilation succeeds perfectly, showing that the change is syntactically valid and that the dataset/assertion configuration compiles correctly using the default fallback database from `dataform.json`.
