---
title: "Resolve 404 Not Found in run_dataform GCP Workflow Step"
project_id: "coc-elt"
nyutu_uuid: "06678309-99d5-43d4-80ca-1260b7052f59"
artifact_type: "Architectural Decision"
tags:
  - "terraform"
  - "gcp-workflows"
  - "dataform"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_resolve-workflow-dataform-404_implementation_plan.md"
---

# Implementation Plan: Resolve 404 Not Found in `run_dataform` Step (Revised)

This implementation plan details the workflow updates required to resolve the 404 Not Found error in the `run_dataform` step of the GCP Workflow, implementing runtime compilation overrides and an asynchronous polling loop for reliable execution monitoring.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following Dataform deployment orchestration requirements:

*   **R1 (Dynamic Compilation)**: The system MUST trigger a compilation of the Dataform repository via HTTP POST to the compilationResults endpoint before execution.
*   **R2 (Compilation Authentication)**: The dynamic compilation request MUST authenticate using OAuth2.
*   **R3 (Git Commitish Specification)**: The dynamic compilation request MUST compile the `"main"` branch/commitish.
*   **R4 (Compilation Config Overrides)**: The dynamic compilation request MUST include the `codeCompilationConfig` object in the POST body to inject `${data_project_id}` as the default database at runtime.
*   **R5 (Dynamic Execution Reference)**: The system MUST invoke the Dataform workflow execution using the dynamic compilation result identifier returned in the compilation response step (`compilation.body.name`).
*   **R6 (Asynchronous Polling Loop)**: The workflow MUST NOT terminate immediately after starting the Dataform invocation; instead, it MUST actively poll the status of the invocation using a loop.
*   **R7 (Status Query)**: During polling, the workflow MUST fetch the status of the invocation via HTTP GET targeting `https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}` authenticated with OAuth2.
*   **R8 (State Evaluation)**: The polling loop MUST check if the state is terminal (`SUCCEEDED`, `FAILED`, `CANCELLED`).
*   **R9 (Failure Propagation)**: IF the terminal state is `FAILED` or `CANCELLED`, THEN the workflow MUST raise an exception to fail the entire GCP Workflow run loudly.
*   **R10 (Validation Safety)**: IF the Terraform configuration is syntax-invalid or references missing resources, THEN the system MUST fail the validation checks.
*   **R11 (Path Parametrization)**: The system MUST construct all Dataform API request URLs using Terraform variables `${data_project_id}` and `${region}` to support multi-environment deployment.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified
*   **Modify**: `terraform/workflow.yaml`

### 2.2 Analysis and Design
Dataform compilation results are transient resources identified by system-generated UUIDs. They cannot be addressed statically.

To solve this and ensure reliable execution:
1. We send a POST request to create a dynamic compilation result, overriding the `defaultDatabase` to target `${data_project_id}` via `codeCompilationConfig`.
2. We run the invocation using the generated compilation result ID.
3. We loop using a sleep interval of 15 seconds, calling HTTP GET to poll the invocation resource status until it reaches a terminal state.
4. We raise an error if the state is not `SUCCEEDED`.

### 2.3 Signatures & Code Changes

#### 2.3.1 Update `terraform/workflow.yaml`
Add compile, run, and polling logic in `terraform/workflow.yaml`:

```yaml
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
    - wait_dataform:
        call: sys.sleep
        args:
          seconds: 15
        next: get_dataform_status
    - get_dataform_status:
        call: http.get
        args:
          url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
          auth:
            type: OAuth2
        result: df_status
    - check_dataform_status:
        switch:
          - condition: $${df_status.body.state == "SUCCEEDED"}
            next: return_result
          - condition: $${df_status.body.state == "FAILED" or df_status.body.state == "CANCELLED"}
            next: raise_dataform_error
        next: wait_dataform
    - raise_dataform_error:
        raise: $${"Dataform workflow invocation " + df_status.body.name + " finished with state: " + df_status.body.state}
    - return_result:
        return: $${df_status.body}
```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Update `terraform/workflow.yaml` to include the `compile_dataform` step with `codeCompilationConfig` overrides.
- [x] T2 — Update `run_dataform` step in `terraform/workflow.yaml` to use `$${compilation.body.name}`.
- [x] T3 — Add the asynchronous polling loop (`wait_dataform`, `get_dataform_status`, `check_dataform_status`, `raise_dataform_error`, `return_result`) in `terraform/workflow.yaml`.
- [x] T4 — Run `terraform validate` inside the `terraform/` directory.
- [x] T5 — Run `terraform plan` inside the `terraform/` directory.
