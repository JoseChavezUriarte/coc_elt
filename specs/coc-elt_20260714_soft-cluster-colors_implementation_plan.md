---
title: "Soft Background Colors for Infrastructure clusters and Gray Edges"
project_id: "coc-elt"
nyutu_uuid: "e2928d0e-eac7-4ea3-b12f-d91f42a6520b"
artifact_type: "Infrastructure Pattern"
tags:
  - "diagrams"
  - "gcp"
  - "elt-architecture"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_soft-cluster-colors_implementation_plan.md"
---

# Implementation Plan - Soft Background Colors for Infrastructure clusters and Gray Edges

This plan describes the implementation of updates to `generate_infra.py` to revert edge colors to 'gray' and apply specific soft background colors (with ~12% transparency) to the 4 nested clusters in the architecture diagram.

---

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Revert Edge Colors)**: The system MUST set all Edge colors to `'gray'` in the diagram.
*   **R2 (Development CI/CD Cluster Background)**: The system MUST set the background color of the `'Development / CI/CD Flow'` cluster to `'#f0f9211f'`.
*   **R3 (Runtime Ingestion Cluster Background)**: The system MUST set the background color of the `'Runtime Ingestion & Orchestration Flow'` cluster to `'#fb9f3a1f'`.
*   **R4 (Data Storage Cluster Background)**: The system MUST set the background color of the `'Data Storage (BigQuery DWH)'` cluster to `'#bd37861f'`.
*   **R5 (Data Transformation Cluster Background)**: The system MUST set the background color of the `'Data Transformation (Dataform)'` cluster to `'#7201a81f'`.
*   **R6 (Cluster Styling)**: The system MUST set the `style` attribute in each of the 4 nested clusters' `graph_attr` dictionary to `'filled'` to ensure background colors are rendered.
*   **R7 (Diagram Compilation)**: The system MUST support compiling the architecture diagram via `uv run generate_infra.py` to produce `coc_elt_architecture.png`.
*   **R8 (Graphviz Check)**: IF the Graphviz `dot` executable is missing from the system path, THEN the system MUST print a descriptive error message and exit with status code 1.
*   **R9 (Unwritable Output File)**: IF the output file `coc_elt_architecture.png` cannot be written due to permissions, THEN the system MUST print a descriptive error message and exit with status code 1.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Impacted
*   `generate_infra.py`: Modify nested cluster instantiation to specify `graph_attr` and update edge color configurations.
*   `coc_elt_architecture.png`: Compiled diagram output.

### 2.2 Analysis and Design
*   **Cluster BG Colors**: The `diagrams` library `Cluster` class exposes a keyword argument `graph_attr` which accepts standard Graphviz cluster attributes. To set the background color, we need:
    - `"bgcolor": "<hex-color-with-alpha>"`
    - `"style": "filled"` (to ensure rendering of the background fill)
*   **Edge Colors**: Revert all sequential `color=colors[...]` mappings back to `color="gray"`.
*   **Cleanup**: Remove the unused `colors` list from the `main()` function to keep code clean.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Modify nested `Cluster` statements in `generate_infra.py` to include `graph_attr` with background colors and style.
- [x] T2 — Update all `Edge` definitions in `generate_infra.py` to use `color="gray"`.
- [x] T3 — Compile the updated architecture diagram by executing `uv run generate_infra.py`.
- [x] T4 — Verify that `coc_elt_architecture.png` has been compiled correctly with gray edges and soft cluster backgrounds.
- [x] T5 — Stage and commit all changes using Git.
