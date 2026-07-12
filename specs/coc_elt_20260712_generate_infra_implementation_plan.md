---
title: "Generate GCP ELT Architecture Diagram"
project_id: "coc-elt"
nyutu_uuid: "b4dda439-e283-464f-8dd5-5ccdf7cfbca6"
artifact_type: "Infrastructure Pattern"
tags:
  - "diagrams"
  - "gcp"
  - "elt-architecture"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_generate_infra_implementation_plan.md"
---

# Implementation Plan - Generate GCP ELT Architecture Diagram

This plan describes the implementation of a Python script `generate_infra.py` to programmatically generate an architecture diagram representing the Clash of Clans ELT pipeline on Google Cloud Platform. The script uses the `diagrams` library.

## 1. Requirements (WHAT is needed)

The following requirements define the behavior and structure for generating the architecture diagram:

* **R1:** The system MUST add `diagrams` to the `dev` dependency group in `pyproject.toml`.
* **R2:** The system MUST support compiling the diagram by running `uv run generate_infra.py`.
* **R3:** The script `generate_infra.py` MUST import the following classes:
  * `Users` from `diagrams.onprem.client`
  * `Github` from `diagrams.onprem.vcs`
  * `Build`, `ContainerRegistry`, and `Scheduler` from `diagrams.gcp.devtools`
  * `Run` from `diagrams.gcp.compute`
  * `Workflows` from `diagrams.gcp.integration`
  * `SecretManager` and `Iam` from `diagrams.gcp.security`
  * `Bigquery` from `diagrams.gcp.analytics`
* **R4:** The diagram MUST model the following nodes:
  * External:
    * Developer: Jose Chavez (`Users`)
    * GitHub Repository: `JoseChavezUriarte/coc_elt` (`Github`)
  * Compute Project:
    * Cloud Build Trigger (`Build`)
    * Artifact Registry (`ContainerRegistry`)
    * Cloud Scheduler (`Scheduler`)
    * Cloud Workflows (`Workflows`)
    * Cloud Run Job (`Run`)
    * Secret Manager (`SecretManager`)
    * Ingestion runner Service Account: `coc-elt-runner` (`Iam`)
  * Data Project:
    * BigQuery Dataset: `coc_bronze` (`Bigquery`)
    * Dataform Repository: `coc-elt` (`Github`)
    * Dataform runner Service Account: `coc-dataform-runner` (`Iam`)
* **R5:** The script MUST group the nodes into the "Compute Project" and "Data Project" clusters, leaving Developer and GitHub Repository outside.
* **R6:** The script MUST connect nodes using `>>` and `Edge` with descriptive labels.
* **R7:** The `Diagram` initialization MUST set `show=False` to prevent headless UI display errors.
* **R8:** WHEN compilation succeeds, the script MUST generate a file named `coc_elt_architecture.png` in the project root.
* **R9:** IF graphviz `dot` executable is missing from the system path, THEN the system MUST print a descriptive error message indicating how to install it.
* **R10:** IF the output path `coc_elt_architecture.png` is not writeable, THEN the system MUST handle the exception and print an error message.
* **R11:** The changes to `pyproject.toml`, `uv.lock`, `generate_infra.py`, and the generated diagram `coc_elt_architecture.png` MUST be committed and registered in Nyutu memory.

## 2. Technical Decisions (HOW it will be built)

### Affected Files
* `pyproject.toml`: Modified to add the `diagrams` dependency in the `dev` group.
* `generate_infra.py`: Created in the project root containing the python code to generate the diagram.
* `coc_elt_architecture.png`: Generated in the project root upon execution.
* `specs/coc_elt_20260712_generate_infra_implementation_plan.md`: Created to document this implementation plan.

### Signatures & Logic
The `generate_infra.py` script will be structured as follows:
```python
import shutil
import sys
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.vcs import Github
from diagrams.gcp.devtools import Build, ContainerRegistry, Scheduler
from diagrams.gcp.compute import Run
from diagrams.gcp.integration import Workflows
from diagrams.gcp.security import SecretManager, Iam
from diagrams.gcp.analytics import Bigquery

def main():
    if not shutil.which("dot"):
        print("Error: 'dot' executable not found. Please install Graphviz (e.g., 'sudo apt-get install graphviz') to compile the diagram.", file=sys.stderr)
        sys.exit(1)

    try:
        with Diagram(
            name="Google Cloud ELT Architecture",
            filename="coc_elt_architecture",
            show=False,
            direction="LR",
        ):
            # Nodes outside clusters
            developer = Users("Jose Chavez\n(Developer)")
            github_repo = Github("GitHub Repository\nJoseChavezUriarte/coc_elt")
            
            # Connect developer to github
            developer >> Edge(label="Pushes code") >> github_repo

            with Cluster("Compute Project"):
                build_trigger = Build("Cloud Build Trigger")
                artifact_registry = ContainerRegistry("Artifact Registry")
                scheduler = Scheduler("Cloud Scheduler")
                workflows = Workflows("Cloud Workflows")
                run_job = Run("Cloud Run Job")
                secret_manager = SecretManager("Secret Manager")
                ingestion_sa = Iam("Ingestion SA\ncoc-elt-runner")

            with Cluster("Data Project"):
                bq_dataset = Bigquery("BigQuery Dataset\n(coc_bronze)")
                dataform_repo = Github("Dataform Repository\n(coc-elt)")
                dataform_sa = Iam("Dataform SA\ncoc-dataform-runner")

            # Infrastructure Relationships
            github_repo >> Edge(label="Triggers build") >> build_trigger
            build_trigger >> Edge(label="Pushes container") >> artifact_registry
            build_trigger >> Edge(label="Deploys/Updates") >> run_job
            
            scheduler >> Edge(label="Triggers hourly") >> workflows
            workflows >> Edge(label="Runs job") >> run_job
            
            ingestion_sa >> Edge(label="Identifies") >> run_job
            run_job >> Edge(label="Retrieves API key") >> secret_manager
            run_job >> Edge(label="Ingests raw data") >> bq_dataset
            
            workflows >> Edge(label="Triggers compilation") >> dataform_repo
            dataform_sa >> Edge(label="Identifies") >> dataform_repo
            dataform_repo >> Edge(label="Transforms tables") >> bq_dataset

    except Exception as e:
        print(f"Error generating diagram: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Error Handling
* The system checks for the presence of the `dot` binary using `shutil.which`. If missing, it exits with a clean message instead of letting `diagrams` raise a confusing sub-process exception.
* General exceptions during diagram generation are caught and logged to standard error.

### Discarded Alternatives
* **Alternative: Using Draw.io or Excalidraw**: Discarded because manually drawing diagrams is not version-controlled, can easily get out of sync, and does not align with "diagrams-as-code" best practices.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `diagrams` dependency to the `dev` group in `pyproject.toml` using `uv add --dev diagrams`.
- [x] T2 — Check if `graphviz` is installed on the local system (run `which dot`).
- [x] T3 — Create the `generate_infra.py` script containing imports and logic to model the GCP ELT architecture.
- [x] T4 — Compile the diagram by running `uv run generate_infra.py`.
- [x] T5 — Verify that the output image file `coc_elt_architecture.png` has been generated and displays correctly.
- [x] T6 — Commit the changes using conventional commit style.
- [x] T7 — Register the new architecture pattern in Nyutu memory using `save_cornerstone.py`.
