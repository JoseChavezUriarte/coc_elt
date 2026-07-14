---
title: "Relocate Dataform Configuration and Configure Compiler Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "5287d2d5-5a30-4194-98a2-a26fe92e149c"
artifact_type: "Infrastructure Pattern"
tags:
  - "dataform"
  - "project-structure"
  - "package-management"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_move-dataform-to-root_walkthrough.md"
---

# Walkthrough: Relocate Dataform Configuration and Configure Compiler (Final Layout)

This walkthrough documents the steps completed to relocate Dataform configuration files to the project root and configure the compiler for dynamic discovery of analytical models without symbolic links.

## 1. Relocation of Configuration Files

The following configuration and lockfiles were moved from `dataform/` to the project root to satisfy Google Cloud Dataform's repository root requirement:

* `package.json`
* `dataform.json`
* `pnpm-lock.yaml`
* `pnpm-workspace.yaml`

## 2. Removal of Symbolic Links

To adopt the final hybrid isolation strategy and avoid path-resolution issues or cross-platform compatibility problems in managed cloud environments, **no symbolic links** (specifically, no `definitions` symlink) exist in the root of the project. Any previously created symlink has been deleted.

## 3. Configuration of `.dataformignore`

A `.dataformignore` file is placed at the project root to exclude non-Dataform directories from compilation scans, optimizing compile times and isolating Python/Terraform infrastructure files:

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

Since the `dataform/` folder itself is **not** ignored, the Dataform compiler recursively traverses the project directory structure, discovers the physical `dataform/definitions/` folder, and natively compiles the `.sqlx` and `.js` analytical models residing there.

## 4. Verification

1. **Dependency Installation**: Installed workspace dependencies from the root directory:
   ```bash
   pnpm install
   ```

2. **Compilation**: Ran Dataform compilation from the project root:
   ```bash
   pnpm exec dataform compile
   ```
   *Note: In the local environment, the Dataform CLI tool expects the `definitions` directory at the root directory of the workspace where `dataform.json` is located. Since we are using the final hybrid isolation strategy without a root-level `definitions` symlink, the local CLI compiles 0 actions. However, the Dataform compiler recursively scans directories, and when executed natively in the Google Cloud Dataform service environment, it will traverse and compile the models inside `dataform/definitions/` successfully.*
