---
title: "Relocate Dataform Configuration and Configure Compiler Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "c668bd4d-47e4-4741-90a3-b223ff3330db"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "project-structure"
  - "package-management"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_move-dataform-to-root_walkthrough.md"
---

# Walkthrough: Relocate Dataform Configuration and Configure Compiler

This walkthrough documents the steps completed to relocate Dataform configuration files to the project root and configure the compiler for dynamic discovery of analytical models.

## 1. Relocation of Configuration Files

The following configuration and lockfiles were moved from `dataform/` to the project root to satisfy Google Cloud Dataform's repository root requirement:

```bash
mv dataform/package.json package.json
mv dataform/dataform.json dataform.json
mv dataform/pnpm-lock.yaml pnpm-lock.yaml
mv dataform/pnpm-workspace.yaml pnpm-workspace.yaml
```

## 2. Symbolic Link for Definitions Discovery

Since Google Cloud Dataform and Dataform CLI strictly require the `definitions/` directory to be located at the root of the project (where `dataform.json` resides), and because the physical `dataform/definitions/` subdirectory must be preserved (Requirement R5), a symbolic link was created at the root to bridge them:

```bash
ln -s dataform/definitions definitions
```

This ensures that the compiler successfully traverses and discovers the analytical `.sqlx` and `.js` files without having to duplicate or relocate the physical folders.

## 3. Configuration of `.dataformignore`

A `.dataformignore` file was created at the project root to exclude non-Dataform directories from compilation scans, optimizing compile times and isolating Python/Terraform infrastructure files:

```text
terraform/
.terraform/
src/
scripts/
tests/
specs/
__pycache__/
.venv/
```

## 4. Verification

1. **Dependency Installation**: Installed workspace dependencies from the root directory:
   ```bash
   pnpm install
   ```

2. **Compilation**: Ran Dataform compilation to verify the 3 actions (1 dataset and 2 assertions) are discovered and compiled:
   ```bash
   pnpm exec dataform compile
   ```

   **Output**:
   ```text
   Compiling...

   Compiled 3 action(s).
   1 dataset(s):
     coc_silver.clan_members [incremental]
   2 assertion(s):
     coc_assertions.coc_silver_clan_members_assertions_uniqueKey_0
     coc_assertions.coc_silver_clan_members_assertions_rowConditions
   ```
