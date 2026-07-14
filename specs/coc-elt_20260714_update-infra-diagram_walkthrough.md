---
title: "Update Architecture Diagram Script Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "60b7622c-1643-4280-b2b5-8e609d7bb04f"
artifact_type: "Walkthrough"
tags:
  - "diagrams"
  - "gcp"
  - "elt-architecture"
  - "walkthrough"
source_uri: "specs/coc-elt_20260714_update-infra-diagram_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-14T09:53:00-05:00
- **Objective**: Implement the approved implementation plan to update the diagram script `generate_infra.py` to support a nested cluster structure, custom node sizes, and NAT egress flows, and compile the diagram to `coc_elt_architecture.png`.

### Executed Commands
- `uv run generate_infra.py` (compiled the diagram definition and regenerated the `coc_elt_architecture.png` image)

### State Mutations
- **Created**:
  - `specs/coc-elt_20260714_update-infra-diagram_walkthrough.md` (this walkthrough document)
- **Modified**:
  - `generate_infra.py` (updated to structure the diagram script with nested projects/flows clusters, custom node sizes, and NAT egress flows)
  - `coc_elt_architecture.png` (regenerated diagram image)
  - `specs/nyutu_index.json` (registered the walkthrough under the newly generated Nyutu UUID)
  - `specs/coc-elt_20260714_update-infra-diagram_implementation_plan.md` (marked implementation tasks T1-T7 as completed)

### Architectural Decisions (ADR) and SOLID
- **Nested Cluster Layout (Refined Structure)**: Restructured nodes inside the `Compute Project` and `Data Project` clusters to reflect specific sub-flows (`Development / CI/CD Flow`, `Runtime Ingestion & Orchestration Flow`, `Data Storage (BigQuery DWH)`, and `Data Transformation (Dataform)`). This improves semantic grouping and visual isolation of components.
- **Hierarchical Dataset Sizing**: Set custom dimensions (`width="1.8"`, `height="1.8"` for the Bronze dataset, and `width="1.1"`, `height="1.1"` for the Silver dataset) to highlight the Bronze layer as the main ingestion target, creating a clear visual hierarchy.
- **Explicit NAT and Whitelisted Egress Modeling**: Added `NAT` and `Internet` nodes to depict egress from the Cloud Run Job via Cloud NAT to the external Clash of Clans API, reflecting security/whitelisting constraints.
- **Robust Graphviz / Write Validation**: Kept Graphviz path verification and added specialized write-exception validation handling for output files to guarantee clear, actionable error reporting.

### Validation Artifacts
- **Image Generation**: Successful execution of `uv run generate_infra.py` generating `coc_elt_architecture.png` in the project root.
