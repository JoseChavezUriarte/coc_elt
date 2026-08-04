---
title: "Update Cloud Workflows to Inject Execution Timestamp Walkthrough"
project_id: "coc-elt"
artifact_type: "Infrastructure Pattern"
tags:
  - "cloud-workflows"
  - "walkthrough"
source_uri: "specs/coc-elt_20260804_update-workflow-execution-timestamp_walkthrough.md"
---

# Walkthrough: Cloud Workflows `execution_timestamp` Injection & Fail-Fast Guardrail

## 1. Summary of Changes
- Updated [`terraform/workflow.yaml`](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/workflow.yaml).
- Added `get_max_date_from_bq` step to query ISO 8601 formatted timestamp using dynamic expression syntax with backticks (`query: $${"SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', MAX(extracted_date)) AS max_date FROM `" + data_project_id + ".coc_silver.clan_member_upgrades`"}`).
- Added `validate_bq_result` fail-fast step to check if `rows` array is missing, empty, or if `rows[0].f[0].v` is null.
- Injected `vars.execution_timestamp: $${bq_result.rows[0].f[0].v}` into `compile_dataform` step's `codeCompilationConfig`.

## 2. Verification
- Validated YAML formatting and Cloud Workflows variable syntax.
- Local Dataform compilation (`pnpm dataform compile`) passed with 0 errors across 48 actions.

## 3. Git Commits
- `5d67e4e`: `feat(workflow): add get_max_date_from_bq step and pass execution_timestamp to Dataform compile`
- `8456737`: `feat(workflow): add validate_bq_result fail-fast step and dynamic table backticks`
