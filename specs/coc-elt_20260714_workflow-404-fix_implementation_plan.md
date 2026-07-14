---
title: "Resolve 404 Error in get_dataform_status GCP Workflow Step"
project_id: "coc-elt"
nyutu_uuid: "9a49e284-3cdb-4f06-aedd-721cee3dff14"
artifact_type: "Bug Fix Logic"
tags:
  - "gcp-workflows"
  - "terraform"
  - "dataform"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_workflow-404-fix_implementation_plan.md"
---

# Implementation Plan: Resolve 404 Error in `get_dataform_status` Step (Revised)

This implementation plan details the configuration updates required to fix the 404 Not Found error in the `get_dataform_status` step of the GCP Workflow.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following requirements:

*   **R1 (URL Expression Evaluation)**: The system MUST define the HTTP GET URL for `get_dataform_status` using single quotes and explicit string concatenation.
*   **R2 (Runtime Variable Substitution)**: The GCP Workflows engine MUST evaluate the concatenated expression at runtime to retrieve the dynamic invocation status.
*   **R3 (Terraform Template Escaping)**: The workflow template MUST use double-dollar escape syntax (`$${...}`) inside single quotes to successfully bypass Terraform's `templatefile` interpolation and deliver the expression to the Cloud Workflows engine.
*   **R4 (HCL Syntax Validation)**: The Terraform configuration MUST pass syntax validation via `terraform validate`.
*   **R5 (Successful Dry-Run)**: The Terraform execution plan MUST generate successfully via `terraform plan` without errors.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified
*   **Modify**: `terraform/workflow.yaml` at [line 56](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/workflow.yaml#L56).

### 2.2 Analysis and Design
In `terraform/workflow.yaml` (processed as a Terraform template), the URL in the `get_dataform_status` step is currently defined as:
```yaml
url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
```

Since the URL string contains a colon (`:`) and is not wrapped in an expression block, it is not parsed as an expression by the GCP Workflows engine. As a result, the engine treats it as a literal string, encoding the `${df_invocation.body.name}` placeholder literally, which leads to a 404 Not Found error when the API request is made.

To resolve this, we wrap the URL in single quotes and use explicit string concatenation:
```yaml
url: '$${"https://dataform.googleapis.com/v1beta1/" + df_invocation.body.name}'
```
This ensures that:
1. The string is wrapped in single quotes to satisfy YAML parsing guidelines when a colon is present.
2. The entire string is treated as an expression block by the GCP Workflows engine.
3. The double dollar signs (`$$`) allow Terraform's `templatefile` function to render the template such that `$${...}` resolves to `${...}` in the output YAML. This shields the template from HCL parsing errors and correctly delivers the runtime expression to GCP Workflows.

### 2.3 Signatures & Code Changes

#### 2.3.1 Modify `terraform/workflow.yaml`
Update [line 56](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/workflow.yaml#L56):
```diff
-          url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
+          url: '$${"https://dataform.googleapis.com/v1beta1/" + df_invocation.body.name}'
```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Modify `terraform/workflow.yaml` at [line 56](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/workflow.yaml#L56) to use the single-quoted string concatenation syntax with double-dollar escaping: `url: '$${"https://dataform.googleapis.com/v1beta1/" + df_invocation.body.name}'`.
- [x] T2 — Run `terraform validate` inside the `terraform/` directory.
- [x] T3 — Run `terraform plan` inside the `terraform/` directory to verify the plan output.
