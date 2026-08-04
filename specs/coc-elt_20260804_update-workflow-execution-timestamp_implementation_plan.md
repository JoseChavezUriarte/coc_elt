---
title: "Update Cloud Workflows to Inject Execution Timestamp into Dataform Compilation"
project_id: "coc-elt"
artifact_type: "Infrastructure Pattern"
tags:
  - "cloud-workflows"
  - "dataform"
  - "bigquery"
  - "terraform"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260804_update-workflow-execution-timestamp_implementation_plan.md"
---

## 1. System Context & Codebase Grounding
- The project `coc_elt` uses GCP Cloud Workflows ([`terraform/workflow.yaml`](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/workflow.yaml)) to orchestrate:
  1. Cloud Run ingestion job execution (`run_job`, `wait_job`).
  2. Dataform project compilation (`compile_dataform`).
  3. Dataform workflow invocation (`run_dataform`, `wait_dataform`).
- Problem Statement: Previously, the Cloud Workflow compiled Dataform without passing the `execution_timestamp` compilation variable. This caused Dataform models relying on execution timestamps (`clan_member_activity_historical.sqlx` and `clan_member_activity_hot.sqlx`) to fall back to hardcoded default values.
- Solution: Inject a BigQuery query step (`get_max_date_from_bq`) between job error checking and Dataform compilation to dynamically retrieve `MAX(extracted_date)` from `coc_silver.clan_member_upgrades` in ISO 8601 format, and pass it via `codeCompilationConfig.vars.execution_timestamp`.

## 2. File Actions
- **Modify File:** `terraform/workflow.yaml`
  - Purpose: Insert `get_max_date_from_bq` step and inject `execution_timestamp` into Dataform compilation payload.
- **Create Walkthrough File:** `specs/coc-elt_20260804_update-workflow-execution-timestamp_walkthrough.md`

## 3. Requirements (EARS Notation)
- **R1 (Step Placement & Transition)**: The system MUST transition from `check_job_error` to `get_max_date_from_bq`.
- **R2 (BigQuery Query Specifications)**:
  - The step `get_max_date_from_bq` MUST invoke `googleapis.bigquery.v2.jobs.query`.
  - The query string MUST be `"SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', MAX(extracted_date)) AS max_date FROM swift-capsule-492817-a7.coc_silver.clan_member_upgrades"`.
  - The API request body MUST explicitly set `useLegacySql: false`.
- **R3 (Dataform Compilation Variable Injection)**:
  - The `compile_dataform` step MUST include a `vars` block inside `codeCompilationConfig`.
  - `vars.execution_timestamp` MUST be assigned `$${bq_result.rows[0].f[0].v}`.
- **R4 (Syntax & Indentation)**: YAML formatting and Cloud Workflows variable escape syntax (`$${...}`) MUST strictly follow Cloud Workflows specifications.

## 4. Technical Decisions & Trade-Offs

1. **BigQuery Direct Query Connector**:
   Calling `googleapis.bigquery.v2.jobs.query` natively within Cloud Workflows eliminates the need for intermediate Cloud Functions or external API calls, executing synchronous BigQuery queries in under a second.

2. **ISO 8601 Timestamp Formatting**:
   Formatting `MAX(extracted_date)` using `%Y-%m-%dT%H:%M:%SZ` guarantees that Dataform's JavaScript block parses `execution_ts` into a valid, standard ISO timestamp string for `DATE('${execution_ts}')` and `TIMESTAMP('${execution_ts}')` operations.

## 5. Workflow YAML Code Snippet

```yaml
    - check_job_error:
        switch:
          - condition: $${"error" in op_status}
            raise: $${op_status.error}
        next: get_max_date_from_bq
    - get_max_date_from_bq:
        call: googleapis.bigquery.v2.jobs.query
        args:
          projectId: "${data_project_id}"
          body:
            query: "SELECT FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', MAX(extracted_date)) AS max_date FROM swift-capsule-492817-a7.coc_silver.clan_member_upgrades"
            useLegacySql: false
        result: bq_result
        next: compile_dataform
    - compile_dataform:
        call: http.post
        args:
          url: https://dataform.googleapis.com/v1beta1/projects/${data_project_id}/locations/${region}/repositories/coc-elt/compilationResults
          auth:
            type: OAuth2
          body:
            gitCommitish: "main"
            codeCompilationConfig:
              defaultDatabase: "${data_project_id}"
              vars:
                execution_timestamp: $${bq_result.rows[0].f[0].v}
        result: compilation
    - run_dataform:
        call: http.post
        args:
          url: https://dataform.googleapis.com/v1beta1/projects/${data_project_id}/locations/${region}/repositories/coc-elt/workflowInvocations
          auth:
            type: OAuth2
          body:
            compilationResult: $${compilation.body.name}
        result: df_invocation
```

## 6. Implementation & Verification Steps
- [x] **T1:** Refactor `terraform/workflow.yaml` to include `get_max_date_from_bq` step and `vars.execution_timestamp`.
- [x] **T2:** Validate local Dataform compilation (`pnpm dataform compile`).
- [x] **T3:** Commit changes to Git repository (`5d67e4e`).
- [ ] **T4:** Create walkthrough spec [`specs/coc-elt_20260804_update-workflow-execution-timestamp_walkthrough.md`](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc-elt_20260804_update-workflow-execution-timestamp_walkthrough.md).
