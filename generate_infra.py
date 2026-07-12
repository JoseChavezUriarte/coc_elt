import sys
from types import ModuleType
try:
    from diagrams.gcp.compute import Run
    gcp_integration = ModuleType("diagrams.gcp.integration")
    # Workflows subclasses Run to inherit standard GCP Compute node traits for drawing
    gcp_integration.Workflows = type("Workflows", (Run,), {})
    sys.modules["diagrams.gcp.integration"] = gcp_integration
except ImportError:
    pass

import shutil
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
