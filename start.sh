#!/bin/bash
# NexusGuard NOC - Start Script
# This script starts all services for the NOC platform

set -e

echo "=========================================="
echo "  NexusGuard NOC - Starting Services"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed.${NC}"
    exit 1
fi

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p prometheus/rules
mkdir -p prometheus/test_data
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p alertmanager
mkdir -p agents/learned_playbooks

# Check for .env file
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}Creating backend .env from example...${NC}"
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        echo -e "${GREEN}Created backend/.env - Please update with production values${NC}"
    fi
fi

# Parse arguments
START_MONITORING=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --with-monitoring) START_MONITORING=true ;;
        -h|--help)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-monitoring   Start with AI monitoring agent"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Start services
echo -e "${YELLOW}Starting Docker services...${NC}"
if [ "$START_MONITORING" = true ]; then
    echo -e "${YELLOW}Including AI Monitoring Agent...${NC}"
    $DOCKER_COMPOSE --profile monitoring up -d --build
else
    $DOCKER_COMPOSE up -d --build
fi

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service status
echo ""
echo "=========================================="
echo "  Service Status"
echo "=========================================="

# Check each service
services=("nexusguard-backend" "nexusguard-frontend" "nexusguard-postgres" "nexusguard-redis" "nexusguard-prometheus" "nexusguard-grafana")

all_healthy=true
for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service is not running${NC}"
        all_healthy=false
    fi
done

# Check monitoring agent if started
if [ "$START_MONITORING" = true ]; then
    if docker ps --filter "name=nexusguard-monitoring-agent" --filter "status=running" | grep -q "nexusguard-monitoring-agent"; then
        echo -e "${GREEN}✓ nexusguard-monitoring-agent is running${NC}"
    else
        echo -e "${YELLOW}⚠ nexusguard-monitoring-agent may still be starting${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "  Access URLs"
echo "=========================================="
echo -e "Frontend:     ${GREEN}http://localhost:3090${NC}"
echo -e "Backend API:  ${GREEN}http://localhost:8090${NC}"
echo -e "API Docs:     ${GREEN}http://localhost:8090/docs${NC}"
echo -e "Prometheus:   ${GREEN}http://localhost:9090${NC}"
echo -e "Grafana:      ${GREEN}http://localhost:3001${NC} (admin/admin123)"
echo -e "Alertmanager: ${GREEN}http://localhost:9093${NC}"
echo ""

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}All services started successfully!${NC}"
    echo ""
    echo "Demo Accounts:"
    echo "  Admin:    admin@nexusguard.io / admin123"
    echo "  Engineer: engineer@nexusguard.io / engineer123"
    echo "  Viewer:   viewer@nexusguard.io / viewer123"
    echo ""
    if [ "$START_MONITORING" = true ]; then
        echo "AI Monitoring Agent:"
        echo "  View logs: docker logs -f nexusguard-monitoring-agent"
        echo "  Learned playbooks: ./agents/learned_playbooks/"
    else
        echo "To start with AI Monitoring Agent:"
        echo "  ./start.sh --with-monitoring"
    fi
else
    echo -e "${YELLOW}Some services may need attention. Check logs with:${NC}"
    echo "  docker compose logs <service-name>"
fi
