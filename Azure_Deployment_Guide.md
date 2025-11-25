# Complete Azure Deployment Guide
## Learning Platform - FastAPI Application

This guide provides step-by-step instructions to deploy the Learning Platform application to a new Azure environment from scratch.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Resource Setup](#azure-resource-setup)
3. [Database Configuration](#database-configuration)
4. [Storage Configuration](#storage-configuration)
5. [Kubernetes Setup](#kubernetes-setup)
6. [Application Deployment](#application-deployment)
7. [DNS and Ingress Configuration](#dns-and-ingress-configuration)
8. [Database Initialization](#database-initialization)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

Install the following tools on your local machine:

```bash
# Azure CLI
winget install Microsoft.AzureCLI

# kubectl
az aks install-cli

# Docker Desktop
winget install Docker.DockerDesktop

# Git (if not already installed)
winget install Git.Git
```

### Required Accounts

- Azure subscription with contributor access
- Domain name (optional, for custom domain)

### Source Code

Ensure you have the application source code:
```bash
git clone <your-repo-url>
cd learning_platform
```

---

## Azure Resource Setup

### Step 1: Login to Azure

```bash
az login
az account set --subscription "<your-subscription-id>"
```

### Step 2: Create Resource Group

```bash
# Set variables
$RESOURCE_GROUP = "learning-platform-rg"
$LOCATION = "eastus"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 3: Create Azure Container Registry (ACR)

```bash
$ACR_NAME = "learningplatformacr"  # Must be globally unique

az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --location $LOCATION

# Enable admin access (for initial setup)
az acr update --name $ACR_NAME --admin-enabled true

# Get ACR credentials
az acr credential show --name $ACR_NAME
```

**Save the credentials** - you'll need them for Docker login.

### Step 4: Create Azure Kubernetes Service (AKS)

```bash
$AKS_NAME = "learning-platform-aks"

# Create AKS cluster with Application Gateway Ingress Controller
az aks create `
  --resource-group $RESOURCE_GROUP `
  --name $AKS_NAME `
  --node-count 2 `
  --node-vm-size Standard_B2s `
  --enable-managed-identity `
  --network-plugin azure `
  --enable-addons ingress-appgw `
  --appgw-name learning-platform-appgw `
  --appgw-subnet-cidr "10.225.0.0/16" `
  --attach-acr $ACR_NAME `
  --enable-oidc-issuer `
  --enable-workload-identity

# Get AKS credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME
```

> **Note**: This creates an AKS cluster with Application Gateway for ingress. Adjust `node-count` and `node-vm-size` based on your needs.

### Step 5: Create Azure Key Vault

```bash
$KEYVAULT_NAME = "learning-platform-kv"  # Must be globally unique

az keyvault create `
  --resource-group $RESOURCE_GROUP `
  --name $KEYVAULT_NAME `
  --location $LOCATION `
  --enable-rbac-authorization false

# Get Key Vault ID
$KEYVAULT_ID = az keyvault show --name $KEYVAULT_NAME --query id -o tsv
```

### Step 6: Configure Workload Identity for Key Vault Access

```bash
# Get AKS OIDC issuer URL
$AKS_OIDC_ISSUER = az aks show --resource-group $RESOURCE_GROUP --name $AKS_NAME --query "oidcIssuerProfile.issuerUrl" -o tsv

# Create managed identity
$IDENTITY_NAME = "learning-platform-identity"
az identity create --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME

# Get identity details
$IDENTITY_CLIENT_ID = az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query 'clientId' -o tsv
$IDENTITY_OBJECT_ID = az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query 'principalId' -o tsv

# Grant Key Vault access to managed identity
az keyvault set-policy `
  --name $KEYVAULT_NAME `
  --object-id $IDENTITY_OBJECT_ID `
  --secret-permissions get list

# Create federated credential
az identity federated-credential create `
  --name learning-platform-federated-credential `
  --identity-name $IDENTITY_NAME `
  --resource-group $RESOURCE_GROUP `
  --issuer $AKS_OIDC_ISSUER `
  --subject system:serviceaccount:learning-platform:learning-platform-sa
```

---

## Database Configuration

### Step 7: Create Azure SQL Database

```bash
$SQL_SERVER_NAME = "learning-platform-sql"  # Must be globally unique
$SQL_ADMIN_USER = "sqladmin"
$SQL_ADMIN_PASSWORD = "YourSecurePassword123!"  # Change this!
$SQL_DB_NAME = "learning_platform"

# Create SQL Server
az sql server create `
  --resource-group $RESOURCE_GROUP `
  --name $SQL_SERVER_NAME `
  --location $LOCATION `
  --admin-user $SQL_ADMIN_USER `
  --admin-password $SQL_ADMIN_PASSWORD

# Configure firewall to allow Azure services
az sql server firewall-rule create `
  --resource-group $RESOURCE_GROUP `
  --server $SQL_SERVER_NAME `
  --name AllowAzureServices `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 0.0.0.0

# Create database
az sql db create `
  --resource-group $RESOURCE_GROUP `
  --server $SQL_SERVER_NAME `
  --name $SQL_DB_NAME `
  --service-objective S0 `
  --backup-storage-redundancy Local
```

### Step 8: Store Database Connection String in Key Vault

```bash
# Build connection string
$CONNECTION_STRING = "mssql+aioodbc://${SQL_ADMIN_USER}:${SQL_ADMIN_PASSWORD}@${SQL_SERVER_NAME}.database.windows.net:1433/${SQL_DB_NAME}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"

# Store in Key Vault
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-SQL-CONNECTION-STRING" `
  --value $CONNECTION_STRING
```

---

## Storage Configuration

### Step 9: Create Azure Storage Account

```bash
$STORAGE_ACCOUNT_NAME = "learningplatformst"  # Must be globally unique, lowercase, no hyphens
$CONTAINER_NAME = "course-thumbnails"

# Create storage account
az storage account create `
  --resource-group $RESOURCE_GROUP `
  --name $STORAGE_ACCOUNT_NAME `
  --location $LOCATION `
  --sku Standard_LRS `
  --kind StorageV2

# Get storage connection string
$STORAGE_CONNECTION_STRING = az storage account show-connection-string `
  --resource-group $RESOURCE_GROUP `
  --name $STORAGE_ACCOUNT_NAME `
  --query connectionString -o tsv

# Create blob container
az storage container create `
  --name $CONTAINER_NAME `
  --connection-string $STORAGE_CONNECTION_STRING `
  --public-access blob
```

### Step 10: Store Storage Credentials in Key Vault

```bash
# Store connection string
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-STORAGE-CONNECTION-STRING" `
  --value $STORAGE_CONNECTION_STRING

# Store account name
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-STORAGE-ACCOUNT-NAME" `
  --value $STORAGE_ACCOUNT_NAME

# Store container name
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "AZURE-STORAGE-CONTAINER" `
  --value $CONTAINER_NAME
```

### Step 11: Generate and Store Session Secret

```bash
# Generate random session secret
$SESSION_SECRET = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Store in Key Vault
az keyvault secret set `
  --vault-name $KEYVAULT_NAME `
  --name "SESSION-SECRET" `
  --value $SESSION_SECRET
```

---

## Kubernetes Setup

### Step 12: Install Secrets Store CSI Driver

```bash
# Enable Secrets Store CSI Driver addon
az aks enable-addons `
  --resource-group $RESOURCE_GROUP `
  --name $AKS_NAME `
  --addons azure-keyvault-secrets-provider
```

### Step 13: Create Kubernetes Namespace

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: learning-platform
```

Apply:
```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 14: Create Service Account

Create `k8s/serviceaccount.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: learning-platform-sa
  namespace: learning-platform
  annotations:
    azure.workload.identity/client-id: "<IDENTITY_CLIENT_ID>"
  labels:
    azure.workload.identity/use: "true"
```

**Replace `<IDENTITY_CLIENT_ID>`** with the value from Step 6.

Apply:
```bash
kubectl apply -f k8s/serviceaccount.yaml
```

### Step 15: Create SecretProviderClass

Create `k8s/secretproviderclass.yaml`:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: learning-platform-secrets
  namespace: learning-platform
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: "<IDENTITY_CLIENT_ID>"
    keyvaultName: "<KEYVAULT_NAME>"
    cloudName: ""
    objects: |
      array:
        - |
          objectName: SESSION-SECRET
          objectType: secret
          objectVersion: ""
        - |
          objectName: AZURE-SQL-CONNECTION-STRING
          objectType: secret
          objectVersion: ""
        - |
          objectName: AZURE-STORAGE-CONNECTION-STRING
          objectType: secret
          objectVersion: ""
        - |
          objectName: AZURE-STORAGE-ACCOUNT-NAME
          objectType: secret
          objectVersion: ""
        - |
          objectName: AZURE-STORAGE-CONTAINER
          objectType: secret
          objectVersion: ""
    tenantId: "<TENANT_ID>"
```

**Replace placeholders**:
- `<IDENTITY_CLIENT_ID>` - from Step 6
- `<KEYVAULT_NAME>` - your Key Vault name
- `<TENANT_ID>` - get with: `az account show --query tenantId -o tsv`

Apply:
```bash
kubectl apply -f k8s/secretproviderclass.yaml
```

---

## Application Deployment

### Step 16: Build and Push Docker Image

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Build image
docker build -t learning-platform:latest .

# Tag image
docker tag learning-platform:latest ${ACR_NAME}.azurecr.io/learning-platform:latest

# Push to ACR
docker push ${ACR_NAME}.azurecr.io/learning-platform:latest
```

### Step 17: Create Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: learning-platform
  namespace: learning-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: learning-platform
  template:
    metadata:
      labels:
        app: learning-platform
        azure.workload.identity/use: "true"
    spec:
      serviceAccountName: learning-platform-sa
      containers:
      - name: learning-platform
        image: <ACR_NAME>.azurecr.io/learning-platform:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENV
          value: "production"
        - name: SESSION_SECRET
          valueFrom:
            secretKeyRef:
              name: learning-platform-secrets-store
              key: SESSION-SECRET
        - name: AZURE_SQL_CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: learning-platform-secrets-store
              key: AZURE-SQL-CONNECTION-STRING
        - name: AZURE_STORAGE_CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: learning-platform-secrets-store
              key: AZURE-STORAGE-CONNECTION-STRING
        - name: AZURE_STORAGE_ACCOUNT_NAME
          valueFrom:
            secretKeyRef:
              name: learning-platform-secrets-store
              key: AZURE-STORAGE-ACCOUNT-NAME
        - name: AZURE_STORAGE_CONTAINER
          valueFrom:
            secretKeyRef:
              name: learning-platform-secrets-store
              key: AZURE-STORAGE-CONTAINER
        volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets-store"
          readOnly: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: secrets-store
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: "learning-platform-secrets"
```

**Replace `<ACR_NAME>`** with your ACR name.

Apply:
```bash
kubectl apply -f k8s/deployment.yaml
```

### Step 18: Create Service

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: learning-platform
  namespace: learning-platform
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  selector:
    app: learning-platform
```

Apply:
```bash
kubectl apply -f k8s/service.yaml
```

### Step 19: Create Ingress

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: learning-platform-ingress
  namespace: learning-platform
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/backend-path-prefix: "/"
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: learning-platform
            port:
              number: 80
```

Apply:
```bash
kubectl apply -f k8s/ingress.yaml
```

---

## DNS and Ingress Configuration

### Step 20: Get Application Gateway Public IP

```bash
# Get Application Gateway public IP
$APPGW_PUBLIC_IP = az network public-ip show `
  --resource-group $RESOURCE_GROUP `
  --name <APPGW_PUBLIC_IP_NAME> `
  --query ipAddress -o tsv

Write-Host "Application Gateway Public IP: $APPGW_PUBLIC_IP"
```

> **Note**: The public IP name is usually `<appgw-name>-appgwpip`. Check in Azure Portal under the Application Gateway resource.

### Step 21: Configure DNS (Optional)

If you have a custom domain:

1. Go to your DNS provider
2. Create an A record pointing to the Application Gateway public IP
3. Update `ingress.yaml` to include your domain:

```yaml
spec:
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: learning-platform
            port:
              number: 80
```

Apply the updated ingress:
```bash
kubectl apply -f k8s/ingress.yaml
```

---

## Database Initialization

### Step 22: Upload Course Thumbnails to Blob Storage

```bash
# Upload thumbnail images
az storage blob upload-batch `
  --destination $CONTAINER_NAME `
  --source ./thumbnails `
  --connection-string $STORAGE_CONNECTION_STRING
```

### Step 23: Seed Database

Get a pod name:
```bash
kubectl get pods -n learning-platform
```

Copy seed script to pod:
```bash
kubectl cp scripts/seed_courses.py learning-platform/<POD_NAME>:/app/ -n learning-platform
```

Execute seed script:
```bash
kubectl exec -n learning-platform <POD_NAME> -- python /app/scripts/seed_courses.py
```

### Step 24: Run Database Migrations

If you have existing users, run the name fields migration:

```bash
kubectl cp migrate_user_names.py learning-platform/<POD_NAME>:/app/ -n learning-platform
kubectl exec -n learning-platform <POD_NAME> -- python /app/migrate_user_names.py
```

Run the created_at migration:

```bash
kubectl cp migrate_created_at.py learning-platform/<POD_NAME>:/app/ -n learning-platform
kubectl exec -n learning-platform <POD_NAME> -- python /app/migrate_created_at.py
```

---

## Verification

### Step 25: Verify Deployment

```bash
# Check pods
kubectl get pods -n learning-platform

# Check service
kubectl get svc -n learning-platform

# Check ingress
kubectl get ingress -n learning-platform

# View pod logs
kubectl logs -n learning-platform <POD_NAME>
```

### Step 26: Test Application

1. **Access the application**:
   - Via Public IP: `http://<APPGW_PUBLIC_IP>`
   - Via Domain: `http://yourdomain.com`

2. **Test key features**:
   - ✅ Homepage loads
   - ✅ Browse courses page works
   - ✅ User registration works
   - ✅ User login works
   - ✅ Dashboard displays correctly
   - ✅ Profile editing works
   - ✅ Course thumbnails load from Azure Blob Storage

---

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <POD_NAME> -n learning-platform

# Check events
kubectl get events -n learning-platform --sort-by='.lastTimestamp'
```

**Common causes**:
- Image pull errors - verify ACR access
- Secret mounting errors - verify Key Vault permissions
- Resource limits - adjust in deployment.yaml

#### Database Connection Errors

```bash
# Verify connection string
kubectl exec -n learning-platform <POD_NAME> -- env | grep AZURE_SQL

# Test from pod
kubectl exec -n learning-platform <POD_NAME> -- python -c "from app.database import engine; print('Connected')"
```

**Common causes**:
- Firewall rules - ensure Azure services are allowed
- Wrong connection string - verify in Key Vault
- SQL Server not accessible - check network configuration

#### Secrets Not Loading

```bash
# Check SecretProviderClass
kubectl describe secretproviderclass learning-platform-secrets -n learning-platform

# Check pod volumes
kubectl describe pod <POD_NAME> -n learning-platform | grep -A 10 "Volumes:"
```

**Common causes**:
- Workload identity not configured correctly
- Key Vault permissions missing
- Wrong tenant ID or client ID

#### Application Gateway Not Working

```bash
# Check ingress
kubectl describe ingress learning-platform-ingress -n learning-platform

# Check Application Gateway backend health
az network application-gateway show-backend-health `
  --resource-group $RESOURCE_GROUP `
  --name learning-platform-appgw
```

**Common causes**:
- Backend pool not healthy - check pod health
- Ingress annotations incorrect
- Application Gateway subnet issues

### Useful Commands

```bash
# Restart deployment
kubectl rollout restart deployment/learning-platform -n learning-platform

# Scale deployment
kubectl scale deployment/learning-platform --replicas=3 -n learning-platform

# View all resources
kubectl get all -n learning-platform

# Delete and recreate pod
kubectl delete pod <POD_NAME> -n learning-platform

# Port forward for local testing
kubectl port-forward -n learning-platform svc/learning-platform 8000:80
```

---

## Post-Deployment Tasks

### Enable HTTPS

1. **Option 1: Azure-managed certificate**
   ```bash
   # Add managed certificate to Application Gateway
   # Follow Azure Portal wizard
   ```

2. **Option 2: Let's Encrypt**
   - Install cert-manager
   - Configure ClusterIssuer
   - Update ingress with TLS configuration

### Enable Monitoring

```bash
# Enable Azure Monitor for AKS
az aks enable-addons `
  --resource-group $RESOURCE_GROUP `
  --name $AKS_NAME `
  --addons monitoring
```

### Configure Backups

```bash
# Azure SQL automated backups are enabled by default
# Configure retention period
az sql db update `
  --resource-group $RESOURCE_GROUP `
  --server $SQL_SERVER_NAME `
  --name $SQL_DB_NAME `
  --backup-storage-redundancy Geo
```

### Set Up CI/CD

Consider setting up Azure DevOps or GitHub Actions for automated deployments:

1. Build Docker image on code push
2. Push to ACR
3. Update Kubernetes deployment
4. Run database migrations if needed

---

## Cost Optimization

### Recommended Settings for Development

- **AKS**: 1-2 nodes, Standard_B2s
- **SQL Database**: S0 or Basic tier
- **Storage**: Standard_LRS
- **Application Gateway**: Standard_v2 (smallest size)

### Recommended Settings for Production

- **AKS**: 3+ nodes with autoscaling, Standard_D2s_v3
- **SQL Database**: S2+ with geo-replication
- **Storage**: Standard_GRS
- **Application Gateway**: Standard_v2 with autoscaling
- **Enable Azure Monitor and Application Insights**

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable Azure AD authentication for SQL
- [ ] Configure network security groups
- [ ] Enable Azure Key Vault soft delete
- [ ] Set up Azure Policy for compliance
- [ ] Enable diagnostic logging
- [ ] Configure alerts for security events
- [ ] Implement rate limiting on Application Gateway
- [ ] Enable Web Application Firewall (WAF)
- [ ] Regular security updates for container images

---

## Support

For issues or questions:
- Check pod logs: `kubectl logs -n learning-platform <POD_NAME>`
- Review Azure Portal for resource health
- Consult Azure documentation
- Review application logs in Azure Monitor

---

**Deployment Complete!** 🎉

Your Learning Platform is now running on Azure Kubernetes Service with Application Gateway ingress, Azure SQL Database, and Azure Blob Storage.
