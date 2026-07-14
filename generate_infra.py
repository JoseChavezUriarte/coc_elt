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
            developer >> Edge(label="Pushes code", color="dimgray") >> github_repo

            with Cluster("Compute Project"):
                with Cluster("Development / CI/CD Flow", graph_attr={"bgcolor": "#f0f9211f", "style": "filled"}):
                    build_trigger = Build("Cloud Build Trigger")
                    artifact_registry = ContainerRegistry("Artifact Registry")
                
                with Cluster("Runtime Ingestion & Orchestration Flow", graph_attr={"bgcolor": "#fb9f3a1f", "style": "filled"}):
                    scheduler = Scheduler("Cloud Scheduler")
                    workflows = Workflows("Cloud Workflows")
                    run_job = Run("Cloud Run Job")
                    secret_manager = SecretManager("Secret Manager")
                    ingestion_sa = Iam("Ingestion SA\ncoc-elt-runner")
                    cloud_nat = NAT("Cloud NAT")

            with Cluster("Data Project"):
                with Cluster("Data Storage (BigQuery DWH)", graph_attr={"bgcolor": "#bd37861f", "style": "filled"}):
                    bq_bronze = Bigquery("Bronze Layer\n(coc_bronze)", width="1.8", height="1.8")
                    bq_silver = Bigquery("Silver Layer\n(coc_silver)", width="1.1", height="1.1")
                
                with Cluster("Data Transformation (Dataform)", graph_attr={"bgcolor": "#7201a81f", "style": "filled"}):
                    dataform_repo = Github("Dataform Repository\n(coc-elt)")
                    dataform_sa = Iam("Dataform SA\ncoc-dataform-runner")

            # Infrastructure Relationships
            github_repo >> Edge(label="Triggers build", color="dimgray") >> build_trigger
            build_trigger >> Edge(label="Pushes container", color="dimgray") >> artifact_registry
            build_trigger >> Edge(label="Deploys/Updates", color="dimgray") >> run_job
            
            scheduler >> Edge(label="Triggers daily (02:00 UTC)", color="dimgray") >> workflows
            workflows >> Edge(label="Runs job", color="dimgray") >> run_job
            
            ingestion_sa >> Edge(label="Identifies", color="dimgray") >> run_job
            run_job >> Edge(label="Retrieves API key", color="dimgray") >> secret_manager
            
            # NAT Egress Flow
            run_job >> Edge(label="Egress", color="dimgray") >> cloud_nat
            cloud_nat >> Edge(label="IP Whitelisted Egress", color="dimgray") >> coc_api
            
            run_job >> Edge(label="Ingests raw data", color="dimgray") >> bq_bronze
            
            workflows >> Edge(label="Triggers compilation", color="dimgray") >> dataform_repo
            dataform_sa >> Edge(label="Identifies", color="dimgray") >> dataform_repo
            
            # Dataform flow reads from Bronze and transforms/writes to Silver
            bq_bronze >> Edge(label="Reads raw data", color="dimgray") >> dataform_repo
            dataform_repo >> Edge(label="Transforms tables", color="dimgray") >> bq_silver

    except PermissionError as e:
        print(f"Error: Output file not writeable due to permission issues: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating diagram: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
