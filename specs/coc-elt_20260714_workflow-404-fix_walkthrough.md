---
title: "Resolve 404 Error in get_dataform_status GCP Workflow Step Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "c467dbcb-fa83-409f-820b-6612751d6615"
artifact_type: "Bug Fix Logic"
tags:
  - "gcp-workflows"
  - "terraform"
  - "dataform"
  - "walkthrough"
source_uri: "specs/coc-elt_20260714_workflow-404-fix_walkthrough.md"
---

# Walkthrough: Resolve 404 Error in `get_dataform_status` Step

This walkthrough documents the modifications made to the GCP Workflow configuration to fix the 404 Not Found error during the Dataform status polling step (`get_dataform_status`).

## 1. Description of the Issue

In the `terraform/workflow.yaml` template, the `get_dataform_status` step previously queried the Dataform API using a literal-concatenated URL string:
```yaml
url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
```

Because the URL string contains a colon (`:`) and was not enclosed in an expression block, the GCP Workflows engine failed to evaluate the `$${df_invocation.body.name}` runtime variable. Instead, the engine processed it as a literal string. Consequently, the call failed with a HTTP `404 Not Found` error.

## 2. Configuration Modification

To fix this, we updated `terraform/workflow.yaml` to wrap the URL in single quotes and perform explicit string concatenation:

```diff
     - get_dataform_status:
         call: http.get
         args:
-          url: https://dataform.googleapis.com/v1beta1/$${df_invocation.body.name}
+          url: '$${"https://dataform.googleapis.com/v1beta1/" + df_invocation.body.name}'
           auth:
             type: OAuth2
         result: df_status
```

* **Expression Wrapping:** Wrapping the entire value in `$${...}` triggers evaluation by the Cloud Workflows engine at runtime.
* **Single Quotes:** Wrapping the value in single quotes satisfies YAML parsing specifications for fields containing colons.
* **Double-Dollar Escaping:** The `$$` syntax is used so that Terraform's `templatefile` function processes the template and outputs `${...}` (the syntax expected by the GCP Workflows engine) rather than trying to interpolate it as a Terraform local/variable.

## 3. Verification

### 3.1 Terraform Validation
Run `terraform validate` in the `terraform/` directory:
```bash
terraform validate
```
Output:
```text
Success! The configuration is valid.
```

### 3.2 Terraform Plan Verification
Run `terraform plan` in the `terraform/` directory to generate the dry-run execution plan:
```bash
terraform plan
```

Output confirmed that the workflow resource `google_workflows_workflow.workflow` will be updated in-place to use the modified dynamic path:
```text
  # google_workflows_workflow.workflow will be updated in-place
  ~ resource "google_workflows_workflow" "workflow" {
...
                - get_dataform_status:
                    call: http.get
                    args:
          -           url: https://dataform.googleapis.com/v1beta1/${df_invocation.body.name}
          +           url: '${"https://dataform.googleapis.com/v1beta1/" + df_invocation.body.name}'
                      auth:
                        type: OAuth2
                    result: df_status
...
    }
```
