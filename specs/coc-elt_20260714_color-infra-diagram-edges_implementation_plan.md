---
title: "Color Infrastructure Diagram Edges and Update Scheduler Label"
project_id: "coc-elt"
nyutu_uuid: "46b726c0-60e7-47c1-8225-f99dec50f0db"
artifact_type: "Infrastructure Pattern"
tags:
  - "diagrams"
  - "gcp"
  - "elt-architecture"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_color-infra-diagram-edges_implementation_plan.md"
---

# Implementation Plan - Color Infrastructure Diagram Edges and Update Scheduler Label

This plan describes the updates to `generate_infra.py` to:
1. Modify the Cloud Scheduler trigger label to match the Daily schedule defined in Terraform.
2. Introduce a list of colors from Plotly's reversed Plasma colormap (`Plasma_r`).
3. Apply these colors to the various diagram connection edges.

---

## 1. Requirements (WHAT is needed) - EARS Notation

*   **R1 (Scheduler Label Update)**: WHEN the script generates the diagram, the system MUST label the Cloud Scheduler to Cloud Workflows connection edge as 'Triggers daily (02:00 UTC)'.
*   **R2 (Hex Colors Array)**: The system MUST define the Plotly Plasma_r hex colors directly in a list in `generate_infra.py`:
    - `#f0f921`
    - `#fdca26`
    - `#fb9f3a`
    - `#ed7953`
    - `#d8576b`
    - `#bd3786`
    - `#9c179e`
    - `#7201a8`
    - `#46039f`
    - `#0d0887`
*   **R3 (Edge Coloring)**: WHEN the script defines connection edges, the system MUST assign colors from the hex colors list sequentially to ensure distinct, sequential edge colors.
*   **R4 (Diagram Compilation)**: WHEN running `uv run generate_infra.py`, the system MUST generate the architecture diagram image `coc_elt_architecture.png` incorporating the new colors and label.
*   **R5 (Missing dot Executable)**: IF the Graphviz `dot` executable is missing from the system path, THEN the system MUST print a descriptive error message and exit with status code 1.
*   **R6 (Output Unwritable)**: IF the output file `coc_elt_architecture.png` cannot be written due to permissions, THEN the system MUST print a descriptive error message and exit with status code 1.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Impacted
- `generate_infra.py`: Update node labels and edge colors.
- `coc_elt_architecture.png`: Compiled output diagram.

### 2.2 Analysis and Design
*   We will define the static list of colors at the beginning of the `main()` function:
    ```python
    colors = [
        "#f0f921",
        "#fdca26",
        "#fb9f3a",
        "#ed7953",
        "#d8576b",
        "#bd3786",
        "#9c179e",
        "#7201a8",
        "#46039f",
        "#0d0887"
    ]
    ```
*   Each edge definition in `generate_infra.py` will be modified to include a `color` attribute, referencing `colors[i % len(colors)]`. This gives a sequential assignment that repeats if there are more than 10 edges (there are 15 edges).
*   For example:
    - Developer to GitHub: `developer >> Edge(label="Pushes code", color=colors[0]) >> github_repo`
    - Cloud Scheduler: `scheduler >> Edge(label="Triggers daily (02:00 UTC)", color=colors[4]) >> workflows`

### 2.3 Discarded Alternatives
- **Dynamic Colormaps**: Using `plotly` or `matplotlib` packages to generate colors dynamically was discarded because it adds unnecessary third-party dependencies to a simple visualization script.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Update the Scheduler trigger label from `'Triggers hourly'` to `'Triggers daily (02:00 UTC)'` in `generate_infra.py`.
- [x] T2 — Define the static list of hex colors `colors` inside the `main()` function of `generate_infra.py`.
- [x] T3 — Add `color=colors[index]` attributes to all 15 connection edges in `generate_infra.py`.
- [x] T4 — Compile the architecture diagram by running `uv run generate_infra.py`.
- [x] T5 — Verify that the generated file `coc_elt_architecture.png` has colored edges and the updated label.
- [x] T6 — Stage and commit all changes using Git.
