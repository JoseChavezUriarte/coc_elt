# Clash of Clans ELT Pipeline

This project provisions a cross-project ELT pipeline on Google Cloud Platform. It extracts Clash of Clans API data, loads it into Google BigQuery Bronze dataset, and uses Dataform to transform the data.

## Deployment Workflow (2-Step Targeted Apply)

Due to Cloud Build v2 GitHub connection requiring interactive user authorization (OAuth), a standard `terraform apply` will fail on the repository creation step. Follow this 2-step targeted deployment workflow:

### Step 1: Target the Connection Creation
First, provision the GitHub connection resource along with its required services and Secret Manager accessor permissions. Run:
```bash
terraform apply -target=google_cloudbuildv2_connection.github_conn
```

### Step 2: Manually Authorize the Connection in GCP Console
1. Navigate to the Google Cloud Console.
2. Go to **Cloud Build** -> **Repositories** -> **2nd Gen** tab.
3. Locate the connection named `coc-elt-connection`.
4. Click on the connection and authenticate/authorize it with your GitHub account.

### Step 3: Run Full Apply
Once the connection is authorized in the UI, complete the infrastructure deployment by running a full apply:
```bash
terraform apply
```
This will safely provision the GitHub repository link, the Cloud Build triggers, and all other pipeline resources.
