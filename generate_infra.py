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
from diagrams.onprem.network import Internet
from diagrams.gcp.devtools import Build, ContainerRegistry, Scheduler
from diagrams.gcp.compute import Run
from diagrams.gcp.integration import Workflows
from diagrams.gcp.security import SecretManager, Iam
from diagrams.gcp.analytics import Bigquery
from diagrams.gcp.network import NAT

def main():
    if not shutil.which("dot"):
        print("Error: 'dot' executable not found. Please install Graphviz (e.g., 'sudo apt-get install graphviz') to compile the diagram.", file=sys.stderr)
        sys.exit(1)

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
            coc_api = Internet("Clash of Clans API")
            
            # Connect developer to github
            developer >> Edge(label="Pushes code", color=colors[0]) >> github_repo

            with Cluster("Compute Project"):
                with Cluster("Development / CI/CD Flow"):
                    build_trigger = Build("Cloud Build Trigger")
                    artifact_registry = ContainerRegistry("Artifact Registry")
                
                with Cluster("Runtime Ingestion & Orchestration Flow"):
                    scheduler = Scheduler("Cloud Scheduler")
                    workflows = Workflows("Cloud Workflows")
                    run_job = Run("Cloud Run Job")
                    secret_manager = SecretManager("Secret Manager")
                    ingestion_sa = Iam("Ingestion SA\ncoc-elt-runner")
                    cloud_nat = NAT("Cloud NAT")

            with Cluster("Data Project"):
                with Cluster("Data Storage (BigQuery DWH)"):
                    bq_bronze = Bigquery("Bronze Layer\n(coc_bronze)", width="1.8", height="1.8")
                    bq_silver = Bigquery("Silver Layer\n(coc_silver)", width="1.1", height="1.1")
                
                with Cluster("Data Transformation (Dataform)"):
                    dataform_repo = Github("Dataform Repository\n(coc-elt)")
                    dataform_sa = Iam("Dataform SA\ncoc-dataform-runner")

            # Infrastructure Relationships
            github_repo >> Edge(label="Triggers build", color=colors[1]) >> build_trigger
            build_trigger >> Edge(label="Pushes container", color=colors[2]) >> artifact_registry
            build_trigger >> Edge(label="Deploys/Updates", color=colors[3]) >> run_job
            
            scheduler >> Edge(label="Triggers daily (02:00 UTC)", color=colors[4]) >> workflows
            workflows >> Edge(label="Runs job", color=colors[5]) >> run_job
            
            ingestion_sa >> Edge(label="Identifies", color=colors[6]) >> run_job
            run_job >> Edge(label="Retrieves API key", color=colors[7]) >> secret_manager
            
            # NAT Egress Flow
            run_job >> Edge(label="Egress", color=colors[8]) >> cloud_nat
            cloud_nat >> Edge(label="IP Whitelisted Egress", color=colors[9]) >> coc_api
            
            run_job >> Edge(label="Ingests raw data", color=colors[0]) >> bq_bronze
            
            workflows >> Edge(label="Triggers compilation", color=colors[1]) >> dataform_repo
            dataform_sa >> Edge(label="Identifies", color=colors[2]) >> dataform_repo
            
            # Dataform flow reads from Bronze and transforms/writes to Silver
            bq_bronze >> Edge(label="Reads raw data", color=colors[3]) >> dataform_repo
            dataform_repo >> Edge(label="Transforms tables", color=colors[4]) >> bq_silver

    except PermissionError as e:
        print(f"Error: Output file not writeable due to permission issues: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating diagram: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
