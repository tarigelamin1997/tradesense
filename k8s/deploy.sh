#!/bin/bash

# Kubernetes Deployment Script for TradeSense
# This script deploys TradeSense to a Kubernetes cluster

set -e

echo "🚀 Deploying TradeSense to Kubernetes..."
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
NAMESPACE="tradesense"
REGISTRY="${DOCKER_REGISTRY:-docker.io/tradesense}"
VERSION="${VERSION:-latest}"

# Function to check if resource exists
resource_exists() {
    kubectl get $1 $2 -n $NAMESPACE &> /dev/null
}

# Step 1: Create namespace
echo -e "\n${YELLOW}1. Creating namespace...${NC}"
if ! resource_exists namespace $NAMESPACE; then
    kubectl apply -f namespace.yaml
    echo -e "${GREEN}✅ Namespace created${NC}"
else
    echo -e "${GREEN}✅ Namespace already exists${NC}"
fi

# Step 2: Install cert-manager (if not installed)
echo -e "\n${YELLOW}2. Checking cert-manager...${NC}"
if ! kubectl get namespace cert-manager &> /dev/null; then
    echo "Installing cert-manager..."
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    echo "Waiting for cert-manager to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager -n cert-manager
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-webhook -n cert-manager
    kubectl wait --for=condition=available --timeout=300s deployment/cert-manager-cainjector -n cert-manager
    echo -e "${GREEN}✅ cert-manager installed${NC}"
else
    echo -e "${GREEN}✅ cert-manager already installed${NC}"
fi

# Step 3: Apply configurations
echo -e "\n${YELLOW}3. Applying configurations...${NC}"
kubectl apply -f configmap.yaml
echo -e "${GREEN}✅ ConfigMap applied${NC}"

# Step 4: Apply secrets (check if exists first)
echo -e "\n${YELLOW}4. Applying secrets...${NC}"
if ! resource_exists secret tradesense-secrets; then
    echo -e "${RED}⚠️  Please update secrets.yaml with actual values before applying!${NC}"
    echo "Press Enter to continue after updating secrets.yaml..."
    read
    kubectl apply -f secrets.yaml
    echo -e "${GREEN}✅ Secrets applied${NC}"
else
    echo -e "${GREEN}✅ Secrets already exist${NC}"
fi

# Step 5: Deploy cert-manager issuers
echo -e "\n${YELLOW}5. Deploying cert-manager issuers...${NC}"
kubectl apply -f cert-manager.yaml
echo -e "${GREEN}✅ Certificate issuers configured${NC}"

# Step 6: Deploy databases
echo -e "\n${YELLOW}6. Deploying databases...${NC}"
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
echo "Waiting for databases to be ready..."
kubectl wait --for=condition=ready --timeout=300s pod -l app=postgres -n $NAMESPACE
kubectl wait --for=condition=ready --timeout=300s pod -l app=redis -n $NAMESPACE
echo -e "${GREEN}✅ Databases deployed${NC}"

# Step 7: Build and push images (if in CI/CD)
echo -e "\n${YELLOW}7. Docker images...${NC}"
if [ "$BUILD_IMAGES" = "true" ]; then
    echo "Building and pushing Docker images..."
    # Backend
    docker build -f ../src/backend/Dockerfile.production -t $REGISTRY/backend:$VERSION ../src/backend
    docker push $REGISTRY/backend:$VERSION
    
    # Frontend
    docker build -f ../frontend/Dockerfile.production -t $REGISTRY/frontend:$VERSION ../frontend
    docker push $REGISTRY/frontend:$VERSION
    
    echo -e "${GREEN}✅ Images built and pushed${NC}"
else
    echo "Skipping image build (using existing images)"
fi

# Step 8: Update image tags in deployments
echo -e "\n${YELLOW}8. Updating image tags...${NC}"
sed -i "s|tradesense/backend:latest|$REGISTRY/backend:$VERSION|g" backend.yaml
sed -i "s|tradesense/frontend:latest|$REGISTRY/frontend:$VERSION|g" frontend.yaml

# Step 9: Deploy applications
echo -e "\n${YELLOW}9. Deploying applications...${NC}"
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/backend -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n $NAMESPACE
echo -e "${GREEN}✅ Applications deployed${NC}"

# Step 10: Deploy ingress
echo -e "\n${YELLOW}10. Deploying ingress...${NC}"
kubectl apply -f ingress.yaml
echo -e "${GREEN}✅ Ingress configured${NC}"

# Step 11: Run database migrations
echo -e "\n${YELLOW}11. Running database migrations...${NC}"
POD=$(kubectl get pod -l app=backend -n $NAMESPACE -o jsonpath="{.items[0].metadata.name}")
kubectl exec -it $POD -n $NAMESPACE -- python -c "
from core.db.session import engine, Base
Base.metadata.create_all(bind=engine)
print('✅ Database migrations completed')
"

# Step 12: Health check
echo -e "\n${YELLOW}12. Running health checks...${NC}"
sleep 30  # Wait for services to stabilize

# Check backend health
BACKEND_POD=$(kubectl get pod -l app=backend -n $NAMESPACE -o jsonpath="{.items[0].metadata.name}")
if kubectl exec $BACKEND_POD -n $NAMESPACE -- curl -f http://localhost:8000/api/v1/monitoring/health; then
    echo -e "\n${GREEN}✅ Backend health check passed${NC}"
else
    echo -e "\n${RED}❌ Backend health check failed${NC}"
fi

# Check frontend health
FRONTEND_POD=$(kubectl get pod -l app=frontend -n $NAMESPACE -o jsonpath="{.items[0].metadata.name}")
if kubectl exec $FRONTEND_POD -n $NAMESPACE -- curl -f http://localhost:3000/health; then
    echo -e "\n${GREEN}✅ Frontend health check passed${NC}"
else
    echo -e "\n${RED}❌ Frontend health check failed${NC}"
fi

# Step 13: Display access information
echo -e "\n${YELLOW}13. Deployment Summary${NC}"
echo "========================================"
kubectl get all -n $NAMESPACE
echo ""
echo "Ingress information:"
kubectl get ingress -n $NAMESPACE
echo ""
echo "To get the load balancer URL:"
echo "kubectl get service tradesense-loadbalancer -n $NAMESPACE"
echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update DNS records to point to the load balancer"
echo "2. Wait for SSL certificates to be issued"
echo "3. Test the application at https://tradesense.com"
echo "4. Monitor logs: kubectl logs -f deployment/backend -n $NAMESPACE"
echo "5. Scale if needed: kubectl scale deployment/backend --replicas=5 -n $NAMESPACE"