# Kubernetes Deployment Checklist

## ✅ Files Updated

### New Files Created:
- **serviceaccount.yaml** - ServiceAccount and ClusterRoleBinding for pod identity

### Files Modified:
- **deployment.yaml** - Added: Pod Identity selector, health probes, resource limits, security context
- **ingress.yaml** - Fixed: Service name mismatch, deprecated ingress class annotation, added modern ingressClassName
- **secretproviderclass.yaml** - Added: SecretObjects to create K8s secrets from mounted files, improved comments

---

## 📋 Pre-Deployment Checklist

Before deploying to your Kubernetes cluster, verify the following:

### 1. **Azure Prerequisites** ✓
- [ ] Key Vault `selfhostedvault` exists in Azure
- [ ] Key Vault contains these secrets:
  - [ ] `session-secret` - FastAPI session secret key
  - [ ] `azure-sql-connection-string` - Azure SQL connection string
  - [ ] `azure-storage-connection-string` - Azure Storage connection string
  - [ ] `azure-storage-container` - Container name for blob storage
- [ ] Managed Identity has access to the Key Vault (with Get, List permissions on Secrets)
- [ ] Tenant ID `784f7653-7880-43d4-8bc3-f77cbbf0e3ab` is correct

### 2. **Cluster Prerequisites** ✓
- [ ] AAD Pod Identity is installed on cluster:
  ```bash
  kubectl get pods -n aad-pod-identity-system
  ```
- [ ] Secrets Store CSI Driver is installed:
  ```bash
  kubectl get pods -n kube-system | grep secrets-store-csi
  ```
- [ ] Ingress Controller (nginx) is installed:
  ```bash
  kubectl get pods -n ingress-nginx
  ```

### 3. **Image Registry** ✓
- [ ] Replace `<YOUR_REGISTRY>/learning-platform:latest` in deployment.yaml with your actual registry
- [ ] Image is built and pushed to registry:
  ```bash
  docker build -t <YOUR_REGISTRY>/learning-platform:latest .
  docker push <YOUR_REGISTRY>/learning-platform:latest
  ```

### 4. **DNS Configuration** ✓
- [ ] Domain `itsyuorapp.online` points to your Ingress IP
- [ ] Or update ingress.yaml with your correct domain name

### 5. **Optional: HTTPS/TLS** (Commented in ingress.yaml)
- [ ] If enabling HTTPS, uncomment the tls section in ingress.yaml
- [ ] Install cert-manager on cluster:
  ```bash
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
  ```
- [ ] Create ClusterIssuer for Let's Encrypt (if needed)

---

## 🚀 Deployment Steps

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Create Pod Identity bindings (Azure-specific)
kubectl apply -f k8s/podidentity.yaml

# 3. Create ServiceAccount and RBAC
kubectl apply -f k8s/serviceaccount.yaml

# 4. Create Secrets Provider Class (Key Vault integration)
kubectl apply -f k8s/secretproviderclass.yaml

# 5. Deploy the application
kubectl apply -f k8s/deployment.yaml

# 6. Create Service
kubectl apply -f k8s/service.yaml

# 7. Create Ingress
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get all -n learning-platform
kubectl logs -n learning-platform deployment/learning-platform -f
```

---

## 🔍 Verification Steps

After deployment, verify everything is working:

```bash
# Check pod status
kubectl get pods -n learning-platform

# Check logs for any issues
kubectl logs -n learning-platform deployment/learning-platform

# Check if secrets mounted correctly
kubectl exec -it <pod-name> -n learning-platform -- ls -la /mnt/secrets/

# Check service endpoints
kubectl get svc -n learning-platform

# Check ingress status
kubectl get ingress -n learning-platform

# Test the application
curl http://itsyuorapp.online  # or your domain
```

---

## 🔧 Troubleshooting

### Pod not starting
```bash
kubectl describe pod <pod-name> -n learning-platform
kubectl logs <pod-name> -n learning-platform
```

### Secrets not mounting
- Verify Pod Identity is installed
- Check if managed identity has Key Vault access
- Verify SecretProviderClass name in deployment matches

### Ingress not routing traffic
```bash
kubectl describe ingress learning-platform-ingress -n learning-platform
kubectl get ingress -n learning-platform -o wide
```

### Database connection failing
- Verify `azure-sql-connection-string` exists in Key Vault
- Check if connection string format is correct for aioodbc driver

---

## 📊 Key Changes Made

| Component | Issue | Fix |
|-----------|-------|-----|
| Service Name | Ingress referenced non-existent service | Changed to `learning-platform` |
| ServiceAccount | Missing, but referenced in deployment | Created with proper RBAC |
| Pod Identity | No selector on pod | Added `aadpodidbinding: learning-platform` label |
| Health Checks | No probes defined | Added readiness & liveness probes |
| Resource Limits | Unbounded resource usage | Added requests & limits |
| Ingress Class | Deprecated annotation | Changed to modern `ingressClassName: nginx` |
| Security | No security context | Added non-root user, read-only root FS option |
| Secrets | No automatic K8s secret creation | Added secretObjects for easier reference |

---

## ⚠️ Important Notes

1. **Session Secret**: The `SESSION_SECRET` is critical for user sessions. Make sure it's strong and unique.

2. **Database**: The app will use Azure SQL in production (when ENV=production). Ensure the connection string is valid.

3. **Replicas**: Currently set to 1. For HA, increase replicas and add PodDisruptionBudget.

4. **Static Files**: App mounts `/app/static` and `/app/templates` - these are ephemeral and will be lost on pod restart. Consider using PVC or serving from blob storage.

5. **Scaling**: For multiple replicas, ensure session affinity or use external session store (Redis).

