---
title: "Rename Bronze Tables Implementation Plan"
project_id: "coc-elt"
nyutu_uuid: "ede11d59-74cd-4153-9660-8c064f55e721"
artifact_type: "Infrastructure Pattern"
tags:
  - "bigquery"
  - "terraform"
  - "python"
  - "dataform"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260712_rename-bronze-tables_implementation_plan.md"
---

# Rename Bronze Tables with "coc_" Prefix

This plan implements renaming all BigQuery tables in the Bronze dataset to have the prefix "coc_".

## 1. Requirements

- **R1 (Terraform Prefix)**: `terraform/bigquery.tf` table resource `table_id` attribute MUST change from `each.key` to `"coc_${each.key}"`.
- **R2 (Python Ingestion Prefix)**: `src/coc_elt/main.py` MUST prepend `"coc_"` to all table names passed to `ingester.ingest_record`.
- **R3 (Python Test Assertions)**: `tests/test_bq_client.py` MUST assert table ID as `"test-project.test_dataset.coc_clan"` instead of `"test-project.test_dataset.clan"`.
- **R4 (Dataform Sources Prefix)**: `dataform/definitions/sources.js` MUST declare table sources with prefix `"coc_"`.

## 2. Technical Decisions

No architectural trade-offs; direct table renaming as requested.

## 3. Implementation Tasks

- [x] T1 — Update `terraform/bigquery.tf` with the new prefix.
- [x] T2 — Update `src/coc_elt/main.py` ingester calls.
- [x] T3 — Update `tests/test_bq_client.py` assertions.
- [x] T4 — Update `dataform/definitions/sources.js` declarations.
- [x] T5 — Run validation (`terraform validate` and `uv run pytest`).
