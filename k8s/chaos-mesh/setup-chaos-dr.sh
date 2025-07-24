#!/bin/bash

# Chaos Mesh and Disaster Recovery Setup Script
# This script installs Chaos Mesh for chaos engineering and configures DR procedures

set -e

# Configuration
CHAOS_NAMESPACE="chaos-mesh"
VELERO_NAMESPACE="velero"
CHAOS_VERSION="2.6.2"
VELERO_VERSION="1.12.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed!"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        error "helm is not installed!"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        warning "AWS CLI is not installed. Required for S3 backup operations."
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster!"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create S3 buckets for backups
create_s3_buckets() {
    log "Creating S3 buckets for backups..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        warning "Skipping S3 bucket creation - AWS CLI not available"
        return
    fi
    
    # Create backup buckets
    BUCKETS=("tradesense-backups" "tradesense-velero-backups")
    
    for bucket in "${BUCKETS[@]}"; do
        if aws s3 ls "s3://${bucket}" 2>/dev/null; then
            warning "Bucket ${bucket} already exists"
        else
            log "Creating bucket ${bucket}..."
            aws s3 mb "s3://${bucket}" || warning "Failed to create bucket ${bucket}"
            
            # Enable versioning
            aws s3api put-bucket-versioning \
                --bucket "${bucket}" \
                --versioning-configuration Status=Enabled || true
            
            # Add lifecycle policy
            cat > /tmp/lifecycle.json << EOF
{
    "Rules": [
        {
            "ID": "DeleteOldBackups",
            "Status": "Enabled",
            "Prefix": "",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
EOF
            aws s3api put-bucket-lifecycle-configuration \
                --bucket "${bucket}" \
                --lifecycle-configuration file:///tmp/lifecycle.json || true
            
            rm /tmp/lifecycle.json
        fi
    done
    
    success "S3 buckets configured"
}

# Install Chaos Mesh
install_chaos_mesh() {
    log "Installing Chaos Mesh..."
    
    # Create namespace
    kubectl apply -f chaos-mesh/namespace.yaml
    
    # Add Chaos Mesh Helm repository
    helm repo add chaos-mesh https://charts.chaos-mesh.org
    helm repo update
    
    # Install Chaos Mesh
    helm upgrade --install chaos-mesh chaos-mesh/chaos-mesh \
        --namespace ${CHAOS_NAMESPACE} \
        --version ${CHAOS_VERSION} \
        --values chaos-mesh/chaos-mesh-values.yaml \
        --wait \
        --timeout 10m
    
    # Wait for components to be ready
    log "Waiting for Chaos Mesh components..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=controller-manager -n ${CHAOS_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=chaos-daemon -n ${CHAOS_NAMESPACE} --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=chaos-dashboard -n ${CHAOS_NAMESPACE} --timeout=300s
    
    success "Chaos Mesh installed"
}

# Install Velero for disaster recovery
install_velero() {
    log "Installing Velero..."
    
    # Create namespace
    kubectl create namespace ${VELERO_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Create credentials secret
    if [ -f "$HOME/.aws/credentials" ]; then
        kubectl create secret generic cloud-credentials \
            --namespace ${VELERO_NAMESPACE} \
            --from-file=cloud=$HOME/.aws/credentials \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        warning "AWS credentials not found. Create manually for Velero."
    fi
    
    # Install Velero using Helm
    helm repo add vmware-tanzu https://vmware-tanzu.github.io/helm-charts
    helm repo update
    
    helm upgrade --install velero vmware-tanzu/velero \
        --namespace ${VELERO_NAMESPACE} \
        --version ${VELERO_VERSION} \
        --set provider=aws \
        --set backupStorageLocation.bucket=tradesense-velero-backups \
        --set backupStorageLocation.config.region=us-east-1 \
        --set volumeSnapshotLocation.config.region=us-east-1 \
        --set secretContents.cloud="$(cat $HOME/.aws/credentials 2>/dev/null || echo '')" \
        --set initContainers[0].name=velero-plugin-for-aws \
        --set initContainers[0].image=velero/velero-plugin-for-aws:v1.8.0 \
        --set initContainers[0].volumeMounts[0].mountPath=/target \
        --set initContainers[0].volumeMounts[0].name=plugins \
        --wait || warning "Velero installation needs manual configuration"
    
    # Apply backup configurations
    kubectl apply -f dr/velero-backup.yaml || warning "Velero backup configuration needs adjustment"
    
    success "Velero installed"
}

# Configure backup jobs
configure_backup_jobs() {
    log "Configuring backup jobs..."
    
    # Create AWS credentials secret for backup jobs
    if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        kubectl create secret generic backup-aws-credentials \
            --namespace tradesense \
            --from-literal=access-key-id="$AWS_ACCESS_KEY_ID" \
            --from-literal=secret-access-key="$AWS_SECRET_ACCESS_KEY" \
            --dry-run=client -o yaml | kubectl apply -f -
    else
        warning "AWS credentials not set. Backup jobs will need manual configuration."
    fi
    
    # Apply backup cronjobs
    kubectl apply -f dr/backup-cronjob.yaml
    
    # Apply restore jobs (they won't run automatically)
    kubectl apply -f dr/restore-job.yaml --dry-run=client || warning "Restore jobs are templates only"
    
    success "Backup jobs configured"
}

# Deploy chaos experiments
deploy_chaos_experiments() {
    log "Deploying chaos experiments..."
    
    # Create experiments directory
    mkdir -p chaos-mesh/experiments
    
    # Apply experiment templates
    for experiment in chaos-mesh/experiments/*.yaml; do
        if [ -f "$experiment" ]; then
            log "Applying experiment: $(basename $experiment)"
            kubectl apply -f "$experiment" --dry-run=client || warning "$(basename $experiment) is a template - modify before use"
        fi
    done
    
    # Apply workflows
    kubectl apply -f chaos-mesh/workflows/gameday-workflow.yaml --dry-run=client || warning "Workflow is a template - review before execution"
    
    success "Chaos experiments deployed (dry-run mode)"
}

# Configure monitoring
configure_monitoring() {
    log "Configuring chaos and DR monitoring..."
    
    # Create Prometheus rules for chaos events
    cat > chaos-prometheus-rules.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: chaos-alerts
  namespace: monitoring
  labels:
    prometheus: kube-prometheus
data:
  chaos.rules.yaml: |
    groups:
    - name: chaos.rules
      interval: 30s
      rules:
      - alert: ChaosExperimentRunning
        expr: chaos_mesh_experiments_total{phase="Running"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Chaos experiment is running"
          description: "Chaos experiment {{ $labels.experiment }} is running in namespace {{ $labels.namespace }}"
      
      - alert: BackupJobFailed
        expr: kube_job_status_failed{job_name=~".*backup.*"} > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Backup job failed"
          description: "Backup job {{ $labels.job_name }} failed in namespace {{ $labels.namespace }}"
      
      - alert: RestoreJobRunning
        expr: kube_job_status_active{job_name=~".*restore.*"} > 0
        for: 1m
        labels:
          severity: info
        annotations:
          summary: "Restore job is running"
          description: "Restore job {{ $labels.job_name }} is active - DR procedure in progress"
EOF
    
    kubectl apply -f chaos-prometheus-rules.yaml
    rm chaos-prometheus-rules.yaml
    
    success "Monitoring configured"
}

# Create documentation
create_documentation() {
    log "Creating documentation..."
    
    # Apply DR runbook
    kubectl apply -f dr/dr-runbook.yaml
    
    cat > CHAOS_DR_GUIDE.md << 'EOF'
# Chaos Engineering and Disaster Recovery Guide

## Overview
This guide covers Chaos Mesh setup for resilience testing and disaster recovery procedures for TradeSense.

## Chaos Engineering

### Running Chaos Experiments

1. **View available experiments**
```bash
kubectl get podchaos,networkchaos,stresschaos,iochaos,timechaos,httpchaos -n chaos-mesh
```

2. **Run a simple pod failure test**
```bash
kubectl apply -f - <<EOF
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: test-pod-failure
  namespace: chaos-mesh
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - tradesense
    labelSelectors:
      app: backend
  duration: "30s"
EOF
```

3. **Monitor experiment**
```bash
# Watch experiment status
kubectl describe podchaos test-pod-failure -n chaos-mesh

# Check application metrics
kubectl port-forward svc/prometheus-server -n monitoring 9090:80
# Open http://localhost:9090
```

4. **Clean up experiment**
```bash
kubectl delete podchaos test-pod-failure -n chaos-mesh
```

### Chaos Dashboard

Access the Chaos Mesh dashboard:
```bash
kubectl port-forward svc/chaos-dashboard -n chaos-mesh 2333:2333
# Open http://localhost:2333
```

### Game Day Procedures

1. **Prepare for Game Day**
   - Notify team members
   - Ensure backups are current
   - Have rollback plan ready

2. **Execute workflow**
```bash
# Review workflow first
kubectl describe workflow tradesense-gameday -n chaos-mesh

# Start workflow
kubectl patch workflow tradesense-gameday -n chaos-mesh --type merge -p '{"spec":{"suspend":false}}'
```

3. **Monitor progress**
   - Watch application metrics
   - Check error rates
   - Monitor user experience

4. **Document findings**
   - What broke?
   - How long to detect?
   - How long to recover?

## Disaster Recovery

### Backup Procedures

1. **Manual backup**
```bash
# PostgreSQL backup
kubectl create job postgres-backup-manual --from=cronjob/postgres-backup -n tradesense

# Velero cluster backup
velero backup create manual-backup --include-namespaces tradesense,monitoring
```

2. **Verify backups**
```bash
# Check backup status
velero backup get
kubectl get jobs -n tradesense | grep backup

# Validate backup content
aws s3 ls s3://tradesense-backups/postgres/ --recursive | tail -5
```

### Recovery Procedures

#### Scenario 1: Database Corruption
```bash
# 1. Stop application
kubectl scale deployment backend --replicas=0 -n tradesense

# 2. Restore database
kubectl apply -f dr/restore-job.yaml
kubectl wait --for=condition=complete job/postgres-restore -n tradesense

# 3. Restart application
kubectl scale deployment backend --replicas=3 -n tradesense
```

#### Scenario 2: Complete Namespace Loss
```bash
# 1. Restore from Velero
velero restore create namespace-restore \
  --from-backup daily-cluster-backup-latest \
  --include-namespaces tradesense

# 2. Wait for resources
kubectl wait --for=condition=ready pod -l app=backend -n tradesense --timeout=600s

# 3. Verify functionality
kubectl exec deploy/backend -n tradesense -- curl -s localhost:8000/health
```

#### Scenario 3: Cluster Failure
```bash
# 1. Create new cluster
eksctl create cluster -f configs/cluster-dr.yaml

# 2. Install Velero
./setup-chaos-dr.sh --velero-only

# 3. Restore everything
velero restore create full-restore \
  --from-backup daily-cluster-backup-latest

# 4. Update DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch file://dns-failover.json
```

### Testing DR Procedures

1. **Monthly DR drill**
```bash
# Create test namespace
kubectl create namespace dr-test

# Test restore
velero restore create test-restore \
  --from-backup daily-cluster-backup-latest \
  --namespace-mappings tradesense:dr-test

# Validate
kubectl get all -n dr-test

# Cleanup
kubectl delete namespace dr-test
```

2. **Backup validation**
```bash
# Run validation script
kubectl create configmap dr-scripts --from-file=dr/scripts/
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: validate-backups
spec:
  template:
    spec:
      containers:
      - name: validator
        image: velero/velero:latest
        command: ["/scripts/validate-backup.sh"]
        volumeMounts:
        - name: scripts
          mountPath: /scripts
      volumes:
      - name: scripts
        configMap:
          name: dr-scripts
          defaultMode: 0755
      restartPolicy: Never
EOF
```

## Best Practices

### Chaos Engineering
1. Start small - single pod failures
2. Gradually increase scope
3. Always have rollback plan
4. Run during business hours
5. Document everything

### Disaster Recovery
1. Test backups regularly
2. Automate recovery procedures
3. Keep runbooks updated
4. Practice communication protocols
5. Measure RTO/RPO regularly

## Monitoring and Alerts

### Key Metrics
- Backup success rate
- Backup size trends
- Recovery time measurements
- Chaos experiment impact

### Alert Examples
```yaml
# Backup failure
alert: BackupFailed
expr: kube_job_status_failed{job_name=~".*backup.*"} > 0
severity: critical

# Long recovery time
alert: RecoveryTimeSLO
expr: recovery_duration_seconds > 7200
severity: warning
```

## Troubleshooting

### Chaos Mesh Issues
```bash
# Check controller logs
kubectl logs -n chaos-mesh -l app.kubernetes.io/component=controller-manager

# Check daemon logs
kubectl logs -n chaos-mesh -l app.kubernetes.io/component=chaos-daemon -c chaos-daemon

# Restart components
kubectl rollout restart deployment chaos-controller-manager -n chaos-mesh
```

### Velero Issues
```bash
# Check Velero logs
kubectl logs deployment/velero -n velero

# Debug backup
velero backup describe <backup-name> --details
velero backup logs <backup-name>

# Force backup deletion
velero backup delete <backup-name> --confirm
```

## Security Considerations

1. **Chaos experiments**
   - Restrict to non-production initially
   - Use RBAC to limit access
   - Audit all experiments

2. **Backup security**
   - Encrypt backups at rest
   - Use IAM roles for access
   - Regular access reviews
   - Test restore permissions

## Links
- [Chaos Mesh Documentation](https://chaos-mesh.org/)
- [Velero Documentation](https://velero.io/)
- [AWS Disaster Recovery](https://aws.amazon.com/disaster-recovery/)
EOF
    
    success "Documentation created: CHAOS_DR_GUIDE.md"
}

# Main execution
main() {
    log "🚀 Starting Chaos Engineering and DR setup..."
    
    check_prerequisites
    
    # Parse arguments
    VELERO_ONLY=false
    CHAOS_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --velero-only)
                VELERO_ONLY=true
                shift
                ;;
            --chaos-only)
                CHAOS_ONLY=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Create S3 buckets
    create_s3_buckets
    
    # Install components
    if [ "$VELERO_ONLY" != "true" ]; then
        install_chaos_mesh
        deploy_chaos_experiments
    fi
    
    if [ "$CHAOS_ONLY" != "true" ]; then
        install_velero
        configure_backup_jobs
    fi
    
    # Configure monitoring
    configure_monitoring
    
    # Create documentation
    create_documentation
    
    success "✨ Chaos Engineering and DR setup complete!"
    log ""
    log "Next steps:"
    log "1. Configure AWS credentials for backups"
    log "2. Test backup and restore procedures"
    log "3. Schedule first chaos game day"
    log "4. Review and customize experiments"
    log "5. Update contact information in runbooks"
    log ""
    log "Access Chaos Dashboard:"
    log "kubectl port-forward svc/chaos-dashboard -n chaos-mesh 2333:2333"
    log ""
    log "View DR runbook:"
    log "kubectl get configmap dr-runbook -n tradesense -o yaml"
}

# Run main function
main "$@"