#!/bin/bash
# NexusGuard NOC - Stop Script
# This script stops all services for the NOC platform

set -e

echo "=========================================="
echo "  NexusGuard NOC - Stopping Services"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine docker compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Parse arguments
REMOVE_VOLUMES=false
REMOVE_IMAGES=false
INCLUDE_MONITORING=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -v|--volumes) REMOVE_VOLUMES=true ;;
        -i|--images) REMOVE_IMAGES=true ;;
        --clean) REMOVE_VOLUMES=true; REMOVE_IMAGES=true ;;
        --with-monitoring) INCLUDE_MONITORING=true ;;
        -h|--help)
            echo "Usage: ./stop.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --volumes       Remove volumes (database data, etc.)"
            echo "  -i, --images        Remove Docker images"
            echo "  --clean             Remove both volumes and images"
            echo "  --with-monitoring   Also stop monitoring agent"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Stop services
echo -e "${YELLOW}Stopping Docker services...${NC}"
if [ "$INCLUDE_MONITORING" = true ]; then
    $DOCKER_COMPOSE --profile monitoring down
else
    $DOCKER_COMPOSE down
fi

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${YELLOW}Removing volumes...${NC}"
    $DOCKER_COMPOSE down -v
    echo -e "${GREEN}Volumes removed${NC}"
fi

if [ "$REMOVE_IMAGES" = true ]; then
    echo -e "${YELLOW}Removing images...${NC}"
    $DOCKER_COMPOSE down --rmi local
    echo -e "${GREEN}Images removed${NC}"
fi

echo ""
echo -e "${GREEN}All services stopped successfully!${NC}"
echo ""
echo "To restart services, run: ./start.sh"
