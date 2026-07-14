---
title: "Update Architecture Diagram Script"
project_id: "coc-elt"
nyutu_uuid: "67b9e9b4-d9dc-46fe-9e6f-e0f27971a1ff"
artifact_type: "Infrastructure Pattern"
tags:
  - "diagrams"
  - "gcp"
  - "elt-architecture"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_update-infra-diagram_implementation_plan.md"
---

# Implementation Plan - Update GCP ELT Architecture Diagram (Revised)

This plan describes the implementation of updates to the Python script `generate_infra.py` to refine the generated GCP ELT architecture diagram according to new structural requirements.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The following requirements define the behavior and structure for the updated architecture diagram:

*   **R1 (Execution Command):** The system MUST support compiling the architecture diagram via `uv run generate_infra.py`.
*   **R2 (Output Name):** The generated diagram MUST name the output file `coc_elt_architecture.png` in the project root.
*   **R3 (Project Boundary Clusters):** The diagram MUST define two top-level clusters representing project boundaries: `Compute Project` and `Data Project`. The project IDs (e.g. `elt-coc`, `swift-capsule-492817-a7`) MUST NOT be included in the labels.
*   **R4 (CI/CD Cluster):** Inside the `Compute Project` cluster, the diagram MUST define a nested cluster for `Development / CI/CD Flow`.
*   **R5 (Ingestion Runtime Cluster):** Inside the `Compute Project` cluster, the diagram MUST define a nested cluster for `Runtime Ingestion & Orchestration Flow`.
*   **R6 (DWH Cluster):** Inside the `Data Project` cluster, the diagram MUST define a nested cluster for `Data Storage (BigQuery DWH)`.
*   **R7 (Dataform Cluster):** Inside the `Data Project` cluster, the diagram MUST define a nested cluster for `Data Transformation (Dataform)`.
*   **R8 (Hierarchical Sizing):** Inside the `Data Storage (BigQuery DWH)` cluster, the diagram MUST prioritize the Bronze layer dataset node and show the Silver layer dataset node as a smaller target by setting custom node width and height attributes (Bronze: 1.8x1.8, Silver: 1.1x1.1).
*   **R9 (NAT Egress Model):** The diagram MUST model network egress from the Cloud Run Job through a Cloud NAT node to an external Clash of Clans API node.
*   **R10 (Whitelist Label):** The edge between the Cloud NAT node and the Clash of Clans API node MUST be labeled to emphasize the IP whitelist requirement.
*   **R11 (Graphviz Verification):** IF the Graphviz `dot` executable is missing from the system path, THEN the system MUST print a descriptive error message indicating how to install it and exit with status code 1.
*   **R12 (IO Exception Handler):** IF the output file `coc_elt_architecture.png` is not writeable, THEN the system MUST handle the exception and print an error message.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Impacted
*   `generate_infra.py`: Modify the script to implement nested clusters, custom node sizes, and new network components.
*   `coc_elt_architecture.png`: Generated in the project root upon script execution.

### 2.2 Analysis and Design
*   **Structure**: We will organize the script to use standard GCP network nodes. Since Cloud NAT is configured as part of a Cloud Router and Cloud NAT has its own dedicated class `NAT` in the `diagrams` library, we will import and declare `NAT` inside `diagrams.gcp.network`.
*   **Project Identification**: As explicitly requested by the user, project IDs (like `elt-coc` or `swift-capsule-492817-a7`) will be omitted from the cluster names to maintain abstract architecture representation.
*   **Top-level Organization**:
    - **Compute Project** cluster will contain:
        - **Development / CI/CD Flow** cluster containing `Build` and `ContainerRegistry`.
        - **Runtime Ingestion & Orchestration Flow** cluster containing `Scheduler`, `Workflows`, `Run`, `SecretManager`, `Iam` (Ingestion SA), and `NAT`.
    - **Data Project** cluster will contain:
        - **Data Storage (BigQuery DWH)** cluster containing `Bigquery` (Bronze) and `Bigquery` (Silver).
        - **Data Transformation (Dataform)** cluster containing `Github` (Dataform Repository) and `Iam` (Dataform SA).
*   **Custom Node Sizes**: Graphviz node dimensions can be set dynamically via keyword arguments passed to the Node constructors:
    - `bq_bronze = Bigquery("Bronze Layer\n(coc_bronze)", width="1.8", height="1.8")`
    - `bq_silver = Bigquery("Silver Layer\n(coc_silver)", width="1.1", height="1.1")`

### 2.3 Code Signature Modifications
Add the following imports to `generate_infra.py`:
```python
from diagrams.onprem.network import Internet
from diagrams.gcp.network import NAT
```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Update imports in `generate_infra.py` to include `NAT` and `Internet`.
- [x] T2 — Define top-level and nested clusters in `generate_infra.py` for both projects and flows (omitting project IDs from labels).
- [x] T3 — Add node instantiation with custom sizes for Bronze and Silver BigQuery datasets in `generate_infra.py`.
- [x] T4 — Add NAT and external Clash of Clans API nodes to `generate_infra.py`.
- [x] T5 — Define connection edges and descriptive labels for egress NAT whitelist in `generate_infra.py`.
- [x] T6 — Compile the updated diagram by running `uv run generate_infra.py`.
- [x] T7 — Verify the visual layout in the generated image `coc_elt_architecture.png`.
