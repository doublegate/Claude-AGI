#!/bin/bash

# Claude-AGI Monitoring Stack Deployment Script
# ============================================
# 
# This script deploys a complete monitoring stack for Claude-AGI including:
# - Prometheus for metrics collection
# - Grafana for visualization
# - Node Exporter for system metrics
# - cAdvisor for container metrics
# - Alertmanager for alert handling

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
MONITORING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$MONITORING_DIR")"

echo -e "${GREEN}🚀 Claude-AGI Monitoring Stack Deployment${NC}"
echo "========================================"
echo "Monitoring directory: $MONITORING_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_status "Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_status "Docker Compose is installed"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi
print_status "Docker daemon is running"

echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p "$MONITORING_DIR/data/prometheus"
mkdir -p "$MONITORING_DIR/data/grafana"
mkdir -p "$MONITORING_DIR/data/alertmanager"
mkdir -p "$MONITORING_DIR/rules"
print_status "Directories created"

# Set proper permissions
echo "Setting permissions..."
sudo chown -R 472:472 "$MONITORING_DIR/data/grafana" 2>/dev/null || {
    print_warning "Could not set Grafana permissions (running as non-root)"
}
sudo chown -R 65534:65534 "$MONITORING_DIR/data/prometheus" 2>/dev/null || {
    print_warning "Could not set Prometheus permissions (running as non-root)"
}
print_status "Permissions configured"

# Validate configuration files
echo "Validating configuration files..."

if [[ ! -f "$MONITORING_DIR/prometheus.yml" ]]; then
    print_error "prometheus.yml not found in $MONITORING_DIR"
    exit 1
fi
print_status "Prometheus configuration found"

if [[ ! -f "$MONITORING_DIR/alertmanager.yml" ]]; then
    print_error "alertmanager.yml not found in $MONITORING_DIR"
    exit 1
fi
print_status "Alertmanager configuration found"

if [[ ! -f "$MONITORING_DIR/docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found in $MONITORING_DIR"
    exit 1
fi
print_status "Docker Compose configuration found"

# Check if services are already running
echo "Checking existing services..."
if docker-compose -f "$MONITORING_DIR/docker-compose.yml" ps | grep -q "Up"; then
    print_warning "Some monitoring services are already running"
    echo -n "Do you want to stop and restart them? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "Stopping existing services..."
        docker-compose -f "$MONITORING_DIR/docker-compose.yml" down
        print_status "Existing services stopped"
    else
        print_error "Deployment cancelled"
        exit 1
    fi
fi

echo ""

# Deploy monitoring stack
echo "Deploying monitoring stack..."
cd "$MONITORING_DIR"

# Pull latest images
echo "Pulling Docker images..."
docker-compose pull
print_status "Docker images updated"

# Start services
echo "Starting monitoring services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check service health
echo "Checking service health..."

# Check Prometheus
if curl -f http://localhost:9090/-/healthy &>/dev/null; then
    print_status "Prometheus is healthy (http://localhost:9090)"
else
    print_warning "Prometheus may not be ready yet"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health &>/dev/null; then
    print_status "Grafana is healthy (http://localhost:3000)"
else
    print_warning "Grafana may not be ready yet"
fi

# Check Node Exporter
if curl -f http://localhost:9100/metrics &>/dev/null; then
    print_status "Node Exporter is healthy (http://localhost:9100)"
else
    print_warning "Node Exporter may not be ready yet"
fi

# Check Alertmanager
if curl -f http://localhost:9093/-/healthy &>/dev/null; then
    print_status "Alertmanager is healthy (http://localhost:9093)"
else
    print_warning "Alertmanager may not be ready yet"
fi

echo ""

# Show service status
echo "Service Status:"
echo "==============="
docker-compose ps

echo ""

# Print access information
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=========================="
echo ""
echo "Access your monitoring services:"
echo ""
echo "📊 Grafana Dashboard:    http://localhost:3000"
echo "   └─ Username: admin"
echo "   └─ Password: admin"
echo ""
echo "📈 Prometheus:           http://localhost:9090"
echo "🔔 Alertmanager:         http://localhost:9093"
echo "🖥️  Node Exporter:        http://localhost:9100"
echo "📦 cAdvisor:             http://localhost:8080"
echo ""
echo "🚀 Claude-AGI App:       http://localhost:8000 (when running)"
echo "📊 App Metrics:          http://localhost:8001/metrics (when running)"
echo ""

# Configuration instructions
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "=============="
echo ""
echo "1. Access Grafana at http://localhost:3000"
echo "   - Login with admin/admin"
echo "   - Change the default password"
echo "   - The Claude-AGI dashboard should be automatically loaded"
echo ""
echo "2. Configure Alertmanager notifications:"
echo "   - Edit monitoring/alertmanager.yml"
echo "   - Configure email/Slack/webhook endpoints"
echo "   - Restart with: docker-compose restart alertmanager"
echo ""
echo "3. Start your Claude-AGI application:"
echo "   - Make sure PROMETHEUS_METRICS_PORT=8001 is set"
echo "   - Make sure METRICS_ENABLED=true is set"
echo "   - Run: python claude-agi.py"
echo ""
echo "4. View logs if needed:"
echo "   - docker-compose logs -f [service-name]"
echo "   - Available services: prometheus, grafana, node-exporter, cadvisor, alertmanager"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "To stop the monitoring stack:"
    echo "  cd $MONITORING_DIR && docker-compose down"
    echo ""
    echo "To remove all data:"
    echo "  cd $MONITORING_DIR && docker-compose down -v"
}

# Register cleanup function
trap cleanup EXIT

print_status "Monitoring stack deployment completed successfully!"

# Optional: Open Grafana in browser
if command -v xdg-open &> /dev/null; then
    echo ""
    echo -n "Open Grafana in your browser now? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        xdg-open "http://localhost:3000" &>/dev/null &
        print_status "Opening Grafana in browser..."
    fi
elif command -v open &> /dev/null; then
    echo ""
    echo -n "Open Grafana in your browser now? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        open "http://localhost:3000" &>/dev/null &
        print_status "Opening Grafana in browser..."
    fi
fi