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
BLUE='\033[0;34m'
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

# Check if Node.js is installed (for local development)
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        echo -e "${GREEN}✓ Node.js ${NODE_VERSION} detected${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Node.js not found (optional for containerized setup)${NC}"
        return 1
    fi
}

# Check if npm is installed
check_npm() {
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}✓ npm ${NPM_VERSION} detected${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ npm not found (optional for containerized setup)${NC}"
        return 1
    fi
}

# Install frontend dependencies if needed
install_frontend_deps() {
    echo ""
    echo -e "${BLUE}Checking frontend dependencies...${NC}"

    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}node_modules not found in frontend/. Installing dependencies...${NC}"

        if check_npm; then
            cd frontend
            echo -e "${YELLOW}Running npm install...${NC}"
            npm install
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ Frontend dependencies installed successfully${NC}"
            else
                echo -e "${RED}✗ Failed to install frontend dependencies${NC}"
                echo -e "${YELLOW}Don't worry - Docker will handle this during build${NC}"
            fi
            cd ..
        else
            echo -e "${YELLOW}npm not available. Dependencies will be installed in Docker container.${NC}"
        fi
    else
        echo -e "${GREEN}✓ Frontend node_modules exists${NC}"

        # Check if package.json is newer than node_modules
        if [ -f "frontend/package.json" ] && [ -f "frontend/package-lock.json" ]; then
            if [ "frontend/package.json" -nt "frontend/node_modules" ] || [ "frontend/package-lock.json" -nt "frontend/node_modules" ]; then
                echo -e "${YELLOW}package.json or package-lock.json is newer than node_modules${NC}"
                echo -e "${YELLOW}Running npm install to update dependencies...${NC}"

                if check_npm; then
                    cd frontend
                    npm install
                    if [ $? -eq 0 ]; then
                        echo -e "${GREEN}✓ Frontend dependencies updated${NC}"
                    fi
                    cd ..
                fi
            fi
        fi
    fi
}

# Check Python dependencies
check_python_deps() {
    echo ""
    echo -e "${BLUE}Checking backend dependencies...${NC}"

    if [ -f "backend/requirements.txt" ]; then
        echo -e "${GREEN}✓ Backend requirements.txt found${NC}"

        if command -v python3 &> /dev/null || command -v python &> /dev/null; then
            PYTHON_CMD=$(command -v python3 || command -v python)
            PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
            echo -e "${GREEN}✓ ${PYTHON_VERSION} detected${NC}"
        else
            echo -e "${YELLOW}⚠ Python not found locally (will use Docker container)${NC}"
        fi
    fi
}

# Create necessary directories
echo ""
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p prometheus/rules
mkdir -p prometheus/test_data
mkdir -p grafana/provisioning/datasources
mkdir -p grafana/provisioning/dashboards
mkdir -p alertmanager
mkdir -p agents/learned_playbooks
mkdir -p ansible/playbooks/learned_playbooks
echo -e "${GREEN}✓ Directories created${NC}"

# Check for .env file
echo ""
echo -e "${BLUE}Checking environment configuration...${NC}"
if [ ! -f backend/.env ]; then
    echo -e "${YELLOW}Creating backend/.env from example...${NC}"
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        echo -e "${GREEN}✓ Created backend/.env - Please update with production values${NC}"
    else
        echo -e "${YELLOW}⚠ backend/.env.example not found${NC}"
    fi
else
    echo -e "${GREEN}✓ Backend .env file exists${NC}"
fi

# Check for frontend .env
if [ ! -f frontend/.env.local ]; then
    if [ -f frontend/.env.example ]; then
        echo -e "${YELLOW}Creating frontend/.env.local from example...${NC}"
        cp frontend/.env.example frontend/.env.local
        echo -e "${GREEN}✓ Created frontend/.env.local${NC}"
    fi
else
    echo -e "${GREEN}✓ Frontend .env.local exists${NC}"
fi

# Run dependency checks
check_node
install_frontend_deps
check_python_deps

# Parse arguments
START_MONITORING=false
FORCE_REBUILD=false
SKIP_DEPS=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --with-monitoring) START_MONITORING=true ;;
        --rebuild) FORCE_REBUILD=true ;;
        --skip-deps) SKIP_DEPS=true ;;
        -h|--help)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --with-monitoring   Start with AI monitoring agent"
            echo "  --rebuild          Force rebuild of Docker images"
            echo "  --skip-deps        Skip dependency check and installation"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start.sh                    # Normal startup"
            echo "  ./start.sh --with-monitoring  # Start with AI agent"
            echo "  ./start.sh --rebuild          # Force rebuild containers"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Start services
echo ""
echo "=========================================="
echo "  Starting Docker Containers"
echo "=========================================="

BUILD_FLAG=""
if [ "$FORCE_REBUILD" = true ]; then
    echo -e "${YELLOW}Force rebuilding Docker images...${NC}"
    BUILD_FLAG="--build --force-recreate"
else
    BUILD_FLAG="--build"
fi

if [ "$START_MONITORING" = true ]; then
    echo -e "${YELLOW}Starting services with AI Monitoring Agent...${NC}"
    $DOCKER_COMPOSE --profile monitoring up -d $BUILD_FLAG
else
    echo -e "${YELLOW}Starting core services...${NC}"
    $DOCKER_COMPOSE up -d $BUILD_FLAG
fi

# Wait for services to be healthy
echo ""
echo -e "${BLUE}Waiting for services to initialize...${NC}"
echo -e "${YELLOW}This may take 30-60 seconds on first run...${NC}"

# Progressive wait with dots
for i in {1..10}; do
    echo -n "."
    sleep 3
done
echo ""

# Check service status
echo ""
echo "=========================================="
echo "  Service Status"
echo "=========================================="

# Enhanced service checking with health status
check_service_health() {
    local service_name=$1
    local container_name=$2
    local port=$3

    if docker ps --filter "name=$container_name" --filter "status=running" | grep -q "$container_name"; then
        # Check if port is accessible (if provided)
        if [ -n "$port" ]; then
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$port > /dev/null 2>&1; then
                echo -e "${GREEN}✓ $service_name is running and healthy (port $port)${NC}"
            else
                echo -e "${YELLOW}⚠ $service_name is running but port $port not ready yet${NC}"
            fi
        else
            echo -e "${GREEN}✓ $service_name is running${NC}"
        fi
        return 0
    else
        echo -e "${RED}✗ $service_name is not running${NC}"
        return 1
    fi
}

# Check each service with health check
all_healthy=true

check_service_health "Backend API" "nexusguard-backend" "8090" || all_healthy=false
check_service_health "Frontend" "nexusguard-frontend" "3090" || all_healthy=false
check_service_health "PostgreSQL" "nexusguard-postgres" "5433" || all_healthy=false
check_service_health "Redis" "nexusguard-redis" "6380" || all_healthy=false
check_service_health "Prometheus" "nexusguard-prometheus" "9090" || all_healthy=false
check_service_health "Grafana" "nexusguard-grafana" "3001" || all_healthy=false
check_service_health "Alertmanager" "nexusguard-alertmanager" "9093" || all_healthy=false
check_service_health "Pushgateway" "nexusguard-pushgateway" "9091" || all_healthy=false

# Check optional services
if docker ps --filter "name=nexusguard-data-generator" --filter "status=running" | grep -q "nexusguard-data-generator"; then
    echo -e "${GREEN}✓ Data Generator is running${NC}"
fi

# Check monitoring agent if started
if [ "$START_MONITORING" = true ]; then
    check_service_health "AI Monitoring Agent" "nexusguard-monitoring-agent" "" || echo -e "${YELLOW}⚠ Monitoring agent may still be initializing${NC}"
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
    echo -e "${GREEN}✓ All services started successfully!${NC}"
    echo ""
    echo "=========================================="
    echo "  Login Credentials"
    echo "=========================================="
    echo "Demo Accounts (for http://localhost:3090/login):"
    echo "  Admin:    admin@nexusguard.io / admin123"
    echo "  Engineer: engineer@nexusguard.io / engineer123"
    echo "  Viewer:   viewer@nexusguard.io / viewer123"
    echo ""
    echo "Grafana:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo ""

    if [ "$START_MONITORING" = true ]; then
        echo "=========================================="
        echo "  AI Monitoring Agent"
        echo "=========================================="
        echo "  View logs:         docker logs -f nexusguard-monitoring-agent"
        echo "  Learned playbooks: ./agents/learned_playbooks/"
        echo "  Stop agent:        docker stop nexusguard-monitoring-agent"
        echo ""
    else
        echo "To start with AI Monitoring Agent:"
        echo "  ./start.sh --with-monitoring"
        echo ""
    fi

    echo "=========================================="
    echo "  Quick Commands"
    echo "=========================================="
    echo "View all logs:        docker compose logs -f"
    echo "View specific logs:   docker compose logs -f backend"
    echo "Stop all services:    docker compose down"
    echo "Restart services:     ./start.sh --rebuild"
    echo "Clean everything:     docker compose down -v"
    echo ""
else
    echo -e "${YELLOW}⚠ Some services need attention${NC}"
    echo ""
    echo "=========================================="
    echo "  Troubleshooting"
    echo "=========================================="
    echo ""
    echo "1. Check service logs:"
    echo "   docker compose logs backend"
    echo "   docker compose logs frontend"
    echo "   docker compose logs postgres"
    echo ""
    echo "2. Check if ports are already in use:"
    echo "   lsof -i :3090  # Frontend"
    echo "   lsof -i :8090  # Backend"
    echo "   lsof -i :5433  # PostgreSQL"
    echo ""
    echo "3. Restart specific service:"
    echo "   docker compose restart backend"
    echo ""
    echo "4. Full restart with rebuild:"
    echo "   ./start.sh --rebuild"
    echo ""
    echo "5. Clean start (WARNING: deletes data):"
    echo "   docker compose down -v"
    echo "   ./start.sh"
    echo ""

    # Show detailed status for failed services
    echo "Failed Service Details:"
    echo "----------------------"
    docker compose ps --filter "status=exited"
    echo ""
fi

echo "=========================================="
echo "  Need Help?"
echo "=========================================="
echo "Documentation: ./README.md"
echo "API Docs:      http://localhost:8090/docs"
echo "Patent Docs:   ./patent/README.md"
echo ""
