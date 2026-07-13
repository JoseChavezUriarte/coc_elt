---
title: "Daily Incremental Upsert Model clan_members in Dataform Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "59fd928e-ea39-4afc-8f4d-2c78cc8b0cd8"
artifact_type: "Data Engineering Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_clan-members_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-13T17:49:12-05:00
- **Objective**: Implement the approved plan to create the daily incremental upsert model `clan_members` under `coc_silver` schema in Dataform.

### Executed Commands
- `npm install` (in `dataform/` directory)
- `npx @dataform/cli@2.9.0 compile` (in `dataform/` directory)

### State Mutations
- **Created**:
  - `dataform/definitions/clan_members.sqlx`
  - `specs/coc-elt_20260713_clan-members_walkthrough.md`
- **Modified**:
  - `specs/coc-elt_20260713_clan-members_implementation_plan.md`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: The model is solely responsible for transforming raw JSON member records from the bronze `coc_members` table into structured, type-safe silver layer rows.
- **Dependency Inversion / Declarative References**: Resolving table dependencies dynamically using `${ref("coc_members")}` rather than hardcoding dataset names.
- **Daily Partitioning & Clustering**: Enforcing query cost controls (FinOps) by partitioning on `extracted_date` and clustering on `ptag` and `role`.
- **Static Lookback Window Filter**: Using `${when(incremental(), ...)}` with a 2-day lookback window ensures partition pruning is leveraged effectively during incremental loads.

### Validation Artifacts
- Successful compilation of the Dataform project.

### Technical Debt
- None identified.
