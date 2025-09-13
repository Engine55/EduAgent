# GCP Setup Script
$PROJECT_ID = "planar-ember-472009-n7"
$REPO = "Engine55/EduAgent"

Write-Host "Starting GCP setup for project: $PROJECT_ID" -ForegroundColor Green

# Create service account
Write-Host "Creating service account..." -ForegroundColor Yellow
gcloud iam service-accounts create github-actions --project=$PROJECT_ID --display-name="GitHub Actions Service Account"

# Grant permissions
Write-Host "Granting permissions..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

# Enable APIs
Write-Host "Enabling APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable iamcredentials.googleapis.com --project=$PROJECT_ID

# Create Artifact Registry
Write-Host "Creating Artifact Registry..." -ForegroundColor Yellow
gcloud artifacts repositories create eduagent-backend --repository-format=docker --location=asia-east1 --project=$PROJECT_ID

# Create Workload Identity Pool
Write-Host "Creating Workload Identity Pool..." -ForegroundColor Yellow
gcloud iam workload-identity-pools create "github-pool" --location="global" --display-name="GitHub Actions Pool" --project=$PROJECT_ID

# Create Workload Identity Provider
Write-Host "Creating Workload Identity Provider..." -ForegroundColor Yellow
gcloud iam workload-identity-pools providers create-oidc "github-provider" --location="global" --workload-identity-pool="github-pool" --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --issuer-uri="https://token.actions.githubusercontent.com" --project=$PROJECT_ID

# Bind service account
Write-Host "Binding service account..." -ForegroundColor Yellow
$projectNumber = (gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
gcloud iam service-accounts add-iam-policy-binding github-actions@${PROJECT_ID}.iam.gserviceaccount.com --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${REPO}" --project=$PROJECT_ID

# Get WIF_PROVIDER value
Write-Host "Getting configuration values..." -ForegroundColor Yellow
$wifProvider = gcloud iam workload-identity-pools providers describe "github-provider" --location="global" --workload-identity-pool="github-pool" --format="value(name)" --project=$PROJECT_ID

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "GitHub Secrets to add:" -ForegroundColor Cyan
Write-Host "GCP_PROJECT_ID = $PROJECT_ID"
Write-Host "WIF_PROVIDER = $wifProvider"
Write-Host "WIF_SERVICE_ACCOUNT = github-actions@${PROJECT_ID}.iam.gserviceaccount.com"