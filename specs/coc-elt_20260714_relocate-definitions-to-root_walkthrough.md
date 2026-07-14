---
title: "Relocate Dataform definitions Folder to Root Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "2e6bf103-f16d-48f3-bab1-a30aee504354"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "project-structure"
  - "bug-fix"
  - "walkthrough"
source_uri: "specs/coc-elt_20260714_relocate-definitions-to-root_walkthrough.md"
---

# Walkthrough: Relocate Dataform definitions Folder to Root

This walkthrough documents the steps completed to relocate the `definitions/` directory from `dataform/definitions/` to the repository root. This ensures that the Dataform compiler natively discovers and compiles the SQLX models, resolving the 400 Bad Request error ("At least one action must be selected") during compilation in Google Cloud Dataform.

## 1. Relocation of the Definitions Directory

The `definitions/` directory containing all SQLX models and JS sources was moved from `dataform/definitions/` to the root of the repository.

* **Before:** `dataform/definitions/`
* **After:** `definitions/`

This puts `definitions/` in the same directory as `dataform.json` (at the root), matching Dataform's default expectation.

## 2. Removal of the Old dataform/ Directory

Once the `definitions/` directory was moved, the `dataform/` directory and any remaining temporary files inside it (such as log files and node modules) were recursively deleted to clean up the repository.

## 3. Dependency Clean-up and Installation

Workspace dependencies were re-installed at the root of the project to ensure clean and correct package references:

```bash
pnpm install
```

## 4. Verification of Compiler Success

To verify that the Dataform compiler compiles all resources correctly from the root, the following command was executed:

```bash
pnpm exec dataform compile
```

The compiler successfully compiled all 3 actions:
* **1 dataset:** `coc_silver.clan_members` (incremental table)
* **2 assertions:** Unique key assertion and row conditions assertion

Output verification:
```text
Compiling...

Compiled 3 action(s).
1 dataset(s):
  coc_silver.clan_members [incremental]
2 assertion(s):
  coc_assertions.coc_silver_clan_members_assertions_uniqueKey_0
  coc_assertions.coc_silver_clan_members_assertions_rowConditions
```
