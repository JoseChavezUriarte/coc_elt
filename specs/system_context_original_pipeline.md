---
title: System Context: Original Dokploy-Based Pipeline Architecture
project_id: coc-elt
nyutu_uuid: 7d8a0c00-8ef4-43f6-8b9e-bc9853bb2643
artifact_type: Architectural Decision
tags:
  - architecture
  - legacy-pipeline
  - docker-compose
  - microservices
source_uri: proyectos/coc_analysis/docs/tutorial/02_architecture_and_docker.md
---
# Original Pipeline Architecture

The legacy system (El Clan-Destino Analytics) was built using a Microservices Architecture composed of four distinct services managed via Docker Compose on a Dokploy-based VPS deployment:

1. **`db` (MongoDB):** A NoSQL document database used to store highly-nested JSON data retrieved from the Clash of Clans API. Data is modeled in collections for `clan`, `warlog`, and `capitalraids`.
2. **`redis` (Redis):** An in-memory database used for caching dashboard calculations to optimize page load speeds.
3. **`dashboard` (Dash by Plotly):** A Python-based interactive web frontend used by clan leadership.
4. **`etl` (Python CLI):** An ephemeral batch ETL pipeline container.

## Ephemeral ETL Container Constraints
- The `etl` container runs once a day via Linux `cron` on the host machine.
- Triggered using `docker compose run --rm etl` to prevent trailing containers.
- Declared under a `"cron"` profile in `docker-compose.yml` to prevent it from starting automatically with the main application stack.
