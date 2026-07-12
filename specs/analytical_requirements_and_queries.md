---
title: Business Logic: Dashboard Analytical Requirements
project_id: coc-elt
nyutu_uuid: 8974b300-5884-4413-9403-66d094314bc7
artifact_type: Business Logic Constraint
tags:
  - requirements
  - business-logic
  - analytical-queries
source_uri: proyectos/coc_analysis/notes/preguntas_a_responder.md
---
# Analytical Requirements

The data pipeline and database schemas must support specific aggregations and visualizations for the Dash frontend:

## Clan Level Metrics
- Total trophy count trends (Main and Builder base).
- Total capital trophies trends.
- Member count evolution.
- Monthly war log statistics (Wars run, wars won, and win-loss ratios).

## Member Level Metrics
- Distribution of members by Town Hall (TH) levels.
- Member activity changes (trophy variations over a given time window $t$ to $t-x$).
- Scatter plots mapping member trophies (main vs builder base) and sizing by Town Hall level.
- Multi-dimensional scatter plots comparing monthly war stars won vs capital raid points contributed.
