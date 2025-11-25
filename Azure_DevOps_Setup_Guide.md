# Azure DevOps CI/CD Setup Guide
## Learning Platform - Continuous Deployment

This guide walks you through setting up Azure DevOps CI/CD pipeline for automated builds and deployments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure DevOps Project Setup](#azure-devops-project-setup)
3. [Service Connections](#service-connections)
4. [Pipeline Configuration](#pipeline-configuration)
5. [Environment Setup](#environment-setup)
6. [First Deployment](#first-deployment)
7. [Pipeline Features](#pipeline-features)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Access

- Azure DevOps organization
- Azure subscription (same one with AKS, ACR, etc.)
- Repository with application code
- Contributor access to Azure resources

### Existing Azure Resources

Ensure you have:
- ✅ Azure Container Registry (ACR)
- ✅ Azure Kubernetes Service (AKS)
- ✅ AKS connected to ACR
- ✅ Application Gateway Ingress Controller
- ✅ Key Vault with secrets

---

## Azure DevOps Project Setup

### Step 1: Create Azure DevOps Organization (if needed)

1. Go to https://dev.azure.com
2. Click "Start free"
3. Sign in with your Microsoft account
4. Create a new organization

### Step 2: Create New Project

1. Click "New Project"
2. **Project name**: `Learning-Platform`
3. **Visibility**: Private
4. **Version control**: Git
5. Click "Create"

### Step 3: Import Repository

**Option A: Import from existing Git repository**

1. Go to **Repos** → **Files**
2. Click "Import repository"
3. **Clone URL**: Your repository URL
4. Click "Import"

**Option B: Push local repository**

```bash
# Add Azure DevOps remote
git remote add azure https://dev.azure.com/<org>/<project>/_git/learning-platform

# Push code
git push azure main
```

---

## Service Connections

Service connections allow Azure DevOps to access your Azure resources.

### Step 4: Create Azure Resource Manager Service Connection

1. Go to **Project Settings** (bottom left)
2. Click **Service connections**
3. Click **New service connection**
4. Select **Azure Resource Manager**
5. Click **Next**

**Authentication method**: Service principal (automatic)

6. **Scope level**: Subscription
7. **Subscription**: Select your Azure subscription
8. **Resource group**: Leave empty (or select specific RG)
9. **Service connection name**: `Azure-Service-Connection`
10. **Grant access permission to all pipelines**: ✅ Check this
11. Click **Save**

### Step 5: Create Docker Registry Service Connection

1. Click **New service connection**
2. Select **Docker Registry**
3. Click **Next**

**Registry type**: Azure Container Registry

4. **Azure subscription**: Select your subscription
5. **Azure container registry**: Select your ACR (`useastacr`)
6. **Service connection name**: `useastacr`
7. **Grant access permission to all pipelines**: ✅ Check this
8. Click **Save**

### Step 6: Create Kubernetes Service Connection

1. Click **New service connection**
2. Select **Kubernetes**
3. Click **Next**

**Authentication method**: Azure Subscription

4. **Azure subscription**: Select your subscription
5. **Cluster**: Select your AKS cluster (`aks-azurecloud`)
6. **Namespace**: `learning-platform`
7. **Service connection name**: `AKS-Service-Connection`
8. **Grant access permission to all pipelines**: ✅ Check this
9. Click **Save**

---

## Pipeline Configuration

### Step 7: Update Pipeline Variables

Edit `azure-pipelines.yml` and update these variables:

```yaml
variables:
  # Update these values
  azureSubscription: 'Azure-Service-Connection'  # Your service connection name
  resourceGroup: 'azurecloud'                     # Your resource group
  acrName: 'useastacr'                           # Your ACR name
  aksCluster: 'aks-azurecloud'                   # Your AKS cluster name
  namespace: 'learning-platform'                  # Your K8s namespace
```

### Step 8: Create Pipeline

1. Go to **Pipelines** → **Pipelines**
2. Click **New pipeline**
3. **Where is your code?**: Azure Repos Git
4. **Select a repository**: learning-platform
5. **Configure your pipeline**: Existing Azure Pipelines YAML file
6. **Path**: `/azure-pipelines.yml`
7. Click **Continue**
8. Review the pipeline
9. Click **Save** (don't run yet)

---

## Environment Setup

### Step 9: Create Production Environment

1. Go to **Pipelines** → **Environments**
2. Click **New environment**
3. **Name**: `production`
4. **Resource**: None (we'll use Kubernetes namespace)
5. Click **Create**

**Optional: Add Approvals**

1. Click on `production` environment
2. Click **⋮** (More options) → **Approvals and checks**
3. Click **Approvals**
4. Add approvers (yourself or team members)
5. Click **Create**

This adds manual approval before production deployment.

---

## First Deployment

### Step 10: Run Pipeline

1. Go to **Pipelines** → **Pipelines**
2. Click on your pipeline
3. Click **Run pipeline**
4. **Branch**: main
5. Click **Run**

**Pipeline Stages**:

1. **Build** - Builds and pushes Docker image to ACR
2. **Deploy** - Deploys to AKS (requires approval if configured)
3. **Migrations** - Runs database migrations (optional)
4. **SmokeTests** - Verifies deployment health

### Step 11: Monitor Pipeline

Watch the pipeline execution:

- ✅ Green checkmark = Success
- ❌ Red X = Failed
- ⏸️ Orange pause = Waiting for approval

Click on each stage to see detailed logs.

---

## Pipeline Features

### Automatic Triggers

**Triggers on**:
- Push to `main` branch
- Push to `develop` branch
- Pull requests to `main`

**Excludes**:
- Changes to `*.md` files
- Changes to `docs/` folder

### Build Stage

1. **Login to ACR** - Authenticates with Azure Container Registry
2. **Build Docker Image** - Uses optimized Dockerfile
3. **Tag Image** - Tags with build ID and `latest`
4. **Push to ACR** - Pushes both tags

**Image naming**:
- `useastacr.azurecr.io/learning-platform:123` (Build ID)
- `useastacr.azurecr.io/learning-platform:latest`

### Deploy Stage

1. **Get AKS Credentials** - Connects to Kubernetes cluster
2. **Deploy Namespace** - Creates/updates namespace
3. **Deploy Service Account** - Sets up workload identity
4. **Deploy Secrets** - Configures Key Vault integration
5. **Deploy Application** - Updates deployment with new image
6. **Wait for Rollout** - Ensures pods are ready
7. **Get Status** - Shows deployment status

**Deployment Strategy**: Rolling update (zero downtime)

### Migrations Stage

Automatically runs database migrations after deployment:
- Copies migration scripts to pod
- Executes migrations
- Continues even if migrations fail (safe)

### Smoke Tests Stage

Verifies deployment health:
- Checks pod status
- Waits for pods to be ready
- Checks application logs
- Tests HTTP endpoint

---

## Advanced Configuration

### Enable Branch Policies

Protect your `main` branch:

1. Go to **Repos** → **Branches**
2. Click **⋮** on `main` → **Branch policies**
3. **Require a minimum number of reviewers**: ✅ Enable (1 reviewer)
4. **Check for linked work items**: ✅ Enable
5. **Build validation**: Add your pipeline
6. Click **Save**

Now all changes to `main` require:
- Pull request
- Code review
- Successful build

### Add Notifications

Get notified of build results:

1. Go to **Project Settings** → **Notifications**
2. Click **New subscription**
3. **Category**: Build
4. **Template**: Build completes
5. **Deliver to**: Your email
6. Click **Finish**

### Multi-Environment Setup

For dev/staging/production:

```yaml
# Add to azure-pipelines.yml
- stage: DeployDev
  condition: eq(variables['Build.SourceBranch'], 'refs/heads/develop')
  # Deploy to dev environment

- stage: DeployStaging
  condition: eq(variables['Build.SourceBranch'], 'refs/heads/staging')
  # Deploy to staging environment

- stage: DeployProd
  condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')
  # Deploy to production environment
```

---

## Troubleshooting

### Pipeline Fails at Build Stage

**Error**: "Docker login failed"

**Solution**:
1. Check ACR service connection
2. Verify ACR name in variables
3. Ensure service principal has ACR push permissions

### Pipeline Fails at Deploy Stage

**Error**: "Unable to connect to AKS"

**Solution**:
1. Check Kubernetes service connection
2. Verify AKS cluster name
3. Ensure service principal has AKS contributor access

### Deployment Succeeds but Pods Crash

**Check**:
```bash
# Get pod logs
kubectl logs -n learning-platform <pod-name>

# Check pod events
kubectl describe pod -n learning-platform <pod-name>
```

**Common causes**:
- Missing secrets in Key Vault
- Wrong environment variables
- Database connection issues

### Image Not Updating in AKS

**Issue**: Deployment shows old image

**Solution**:
```bash
# Force pod restart
kubectl rollout restart deployment/learning-platform -n learning-platform

# Or delete pods
kubectl delete pods -n learning-platform -l app=learning-platform
```

### Service Connection Expired

**Error**: "Service connection authorization failed"

**Solution**:
1. Go to **Project Settings** → **Service connections**
2. Click on the connection
3. Click **Verify**
4. If failed, click **Edit** → **Verify and save**

---

## Best Practices

### 1. Use Build Variables

Store sensitive data in pipeline variables:

1. Go to **Pipelines** → **Library**
2. Click **+ Variable group**
3. Add variables
4. Mark as secret (🔒)
5. Link to pipeline

### 2. Enable Retention Policies

Keep builds for compliance:

1. Go to **Project Settings** → **Retention**
2. Set retention days (e.g., 30 days)
3. Keep artifacts for important builds

### 3. Use YAML Templates

For reusable pipeline code:

```yaml
# templates/build-template.yml
steps:
  - task: Docker@2
    # ...

# azure-pipelines.yml
stages:
  - template: templates/build-template.yml
```

### 4. Add Health Checks

Monitor deployment health:

```yaml
- script: |
    # Wait for app to be healthy
    for i in {1..30}; do
      if curl -f http://localhost:8000/health; then
        echo "App is healthy"
        exit 0
      fi
      sleep 10
    done
    exit 1
  displayName: 'Health Check'
```

---

## Pipeline Workflow

```
┌─────────────────┐
│  Code Push to   │
│   main branch   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Stage    │
│  - Build image  │
│  - Push to ACR  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Deploy Stage   │
│  - Update AKS   │
│  - Wait ready   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Migrations     │
│  - Run scripts  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Smoke Tests    │
│  - Health check │
│  - Verify pods  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   ✅ Success!   │
│  App deployed   │
└─────────────────┘
```

---

## Monitoring Deployments

### View Deployment History

1. Go to **Pipelines** → **Environments**
2. Click **production**
3. See all deployments with:
   - Build number
   - Commit message
   - Deployed by
   - Status

### Rollback to Previous Version

If deployment fails:

```bash
# Find previous image tag
az acr repository show-tags --name useastacr --repository learning-platform

# Update deployment
kubectl set image deployment/learning-platform \
  learning-platform=useastacr.azurecr.io/learning-platform:<previous-tag> \
  -n learning-platform
```

Or use Azure DevOps:
1. Go to failed deployment
2. Click **Redeploy** on last successful run

---

## Next Steps

✅ **Pipeline is now set up!**

Every push to `main` will:
1. Build optimized Docker image (469MB)
2. Push to Azure Container Registry
3. Deploy to AKS automatically
4. Run health checks
5. Notify you of results

**Recommended**:
- Set up staging environment
- Add automated tests
- Configure monitoring alerts
- Enable Application Insights

---

## Support

**Pipeline Issues**:
- Check pipeline logs in Azure DevOps
- Review service connection permissions
- Verify Azure resource access

**Deployment Issues**:
- Check pod logs: `kubectl logs -n learning-platform <pod>`
- Review events: `kubectl get events -n learning-platform`
- Check ingress: `kubectl describe ingress -n learning-platform`

---

**Congratulations!** 🎉

Your Learning Platform now has full CI/CD automation with Azure DevOps!
