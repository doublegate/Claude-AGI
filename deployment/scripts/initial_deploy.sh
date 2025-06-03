#!/bin/bash
# deployment/scripts/initial_deploy.sh

set -e

echo "Claude AGI Initial Deployment Script"
echo "===================================="

# 1. Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        echo "ERROR: Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check required tools
    for tool in helm docker python3; do
        if ! command -v $tool &> /dev/null; then
            echo "ERROR: $tool is not installed"
            exit 1
        fi
    done
    
    echo "✓ Prerequisites satisfied"
}

# 2. Create namespace
create_namespace() {
    echo "Creating namespace..."
    kubectl create namespace claude-system --dry-run=client -o yaml | kubectl apply -f -
    echo "✓ Namespace created"
}

# 3. Install infrastructure
install_infrastructure() {
    echo "Installing infrastructure components..."
    
    # Install Redis
    helm install redis bitnami/redis \
        --namespace claude-system \
        --set auth.enabled=false \
        --set replica.replicaCount=3
    
    # Install PostgreSQL
    helm install postgres bitnami/postgresql \
        --namespace claude-system \
        --set auth.postgresPassword=$POSTGRES_PASSWORD \
        --set primary.persistence.size=100Gi
    
    # Install monitoring stack
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace claude-system
    
    echo "✓ Infrastructure installed"
}

# 4. Initialize databases
initialize_databases() {
    echo "Initializing databases..."
    
    # Wait for PostgreSQL to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=postgresql \
        --namespace claude-system --timeout=300s
    
    # Run migrations
    kubectl run migrations --rm -i --restart=Never \
        --namespace claude-system \
        --image=claude-agi:latest \
        -- python -m src.database.migrations
    
    echo "✓ Databases initialized"
}

# 5. Deploy Claude AGI
deploy_claude() {
    echo "Deploying Claude AGI..."
    
    # Apply configurations
    kubectl apply -f deployment/kubernetes/configmap.yaml
    kubectl apply -f deployment/kubernetes/secrets.yaml
    kubectl apply -f deployment/kubernetes/pvc.yaml
    kubectl apply -f deployment/kubernetes/claude-agi-deployment.yaml
    kubectl apply -f deployment/kubernetes/services.yaml
    
    # Wait for deployment
    kubectl wait --for=condition=available deployment/claude-agi \
        --namespace claude-system --timeout=600s
    
    echo "✓ Claude AGI deployed"
}

# 6. Verify deployment
verify_deployment() {
    echo "Verifying deployment..."
    
    # Check pod status
    kubectl get pods -n claude-system
    
    # Check logs
    kubectl logs -n claude-system -l app=claude-agi --tail=50
    
    # Test health endpoint
    kubectl port-forward -n claude-system service/claude-agi-service 8000:8000 &
    sleep 5
    
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        echo "✓ Deployment verified - Claude AGI is running!"
    else
        echo "✗ Deployment verification failed"
        exit 1
    fi
}

# Main execution
check_prerequisites
create_namespace
install_infrastructure
initialize_databases
deploy_claude
verify_deployment

echo "Deployment complete! Claude AGI is now running."