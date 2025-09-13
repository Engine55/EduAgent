# GCP自动化配置脚本
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$true)]
    [string]$GitHubRepo
)

Write-Host "🚀 开始配置GCP项目: $ProjectId" -ForegroundColor Green
Write-Host "📁 GitHub仓库: $GitHubRepo" -ForegroundColor Green

# 1. 创建服务账号
Write-Host "1️⃣ 创建服务账号..." -ForegroundColor Yellow
gcloud iam service-accounts create github-actions --project=$ProjectId --display-name="GitHub Actions Service Account"

# 2. 授予权限
Write-Host "2️⃣ 授予权限..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:github-actions@${ProjectId}.iam.gserviceaccount.com" --role="roles/run.admin"
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:github-actions@${ProjectId}.iam.gserviceaccount.com" --role="roles/storage.admin"
gcloud projects add-iam-policy-binding $ProjectId --member="serviceAccount:github-actions@${ProjectId}.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"

# 3. 启用APIs
Write-Host "3️⃣ 启用APIs..." -ForegroundColor Yellow
gcloud services enable run.googleapis.com --project=$ProjectId
gcloud services enable artifactregistry.googleapis.com --project=$ProjectId
gcloud services enable iamcredentials.googleapis.com --project=$ProjectId

# 4. 创建Artifact Registry
Write-Host "4️⃣ 创建Artifact Registry..." -ForegroundColor Yellow
gcloud artifacts repositories create eduagent-backend --repository-format=docker --location=asia-east1 --project=$ProjectId

# 5. 创建Workload Identity Pool
Write-Host "5️⃣ 创建Workload Identity Pool..." -ForegroundColor Yellow
gcloud iam workload-identity-pools create "github-pool" --location="global" --display-name="GitHub Actions Pool" --project=$ProjectId

# 6. 创建Workload Identity Provider
Write-Host "6️⃣ 创建Workload Identity Provider..." -ForegroundColor Yellow
gcloud iam workload-identity-pools providers create-oidc "github-provider" --location="global" --workload-identity-pool="github-pool" --display-name="GitHub Actions Provider" --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" --issuer-uri="https://token.actions.githubusercontent.com" --project=$ProjectId

# 7. 绑定服务账号
Write-Host "7️⃣ 绑定服务账号..." -ForegroundColor Yellow
$projectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)")
gcloud iam service-accounts add-iam-policy-binding github-actions@${ProjectId}.iam.gserviceaccount.com --role="roles/iam.workloadIdentityUser" --member="principalSet://iam.googleapis.com/projects/${projectNumber}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GitHubRepo}" --project=$ProjectId

# 8. 获取配置信息
Write-Host "8️⃣ 获取GitHub Secrets配置..." -ForegroundColor Yellow
$wifProvider = gcloud iam workload-identity-pools providers describe "github-provider" --location="global" --workload-identity-pool="github-pool" --format="value(name)" --project=$ProjectId

Write-Host "✅ 配置完成！" -ForegroundColor Green
Write-Host ""
Write-Host "🔑 请在GitHub仓库设置以下Secrets:" -ForegroundColor Cyan
Write-Host "GCP_PROJECT_ID = $ProjectId"
Write-Host "WIF_PROVIDER = $wifProvider"
Write-Host "WIF_SERVICE_ACCOUNT = github-actions@${ProjectId}.iam.gserviceaccount.com"
Write-Host "OPENAI_API_KEY = 你的OpenAI API Key"
Write-Host "DATABASE_URL = 你的数据库连接字符串"