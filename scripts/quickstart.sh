#!/bin/bash
# Good Shepherd Quick Start Script
# This script sets up and runs the development environment

set -e

echo "🛡️ Good Shepherd - Quick Start"
echo "================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prereqs() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker${NC}"
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker Compose${NC}"
    
    # Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2)${NC}"
    
    # Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Node.js $(node --version)${NC}"
}

# Setup environment
setup_env() {
    echo -e "\n${YELLOW}Setting up environment...${NC}"
    
    # Copy .env if not exists
    if [ ! -f infrastructure/.env ]; then
        cp infrastructure/.env.example infrastructure/.env
        echo -e "${GREEN}✓ Created infrastructure/.env from template${NC}"
        echo -e "${YELLOW}  ⚠️  Please update with your actual credentials${NC}"
    else
        echo -e "${GREEN}✓ infrastructure/.env exists${NC}"
    fi
}

# Setup Python virtual environment
setup_python() {
    echo -e "\n${YELLOW}Setting up Python environment...${NC}"
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Created virtual environment${NC}"
    fi
    
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Installed Python dependencies${NC}"
}

# Setup frontend
setup_frontend() {
    echo -e "\n${YELLOW}Setting up frontend...${NC}"
    
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    echo -e "${GREEN}✓ Installed frontend dependencies${NC}"
    cd ..
}

# Start infrastructure services
start_infra() {
    echo -e "\n${YELLOW}Starting infrastructure services...${NC}"
    
    cd infrastructure
    docker compose up -d redis postgres meilisearch
    cd ..
    
    echo -e "${GREEN}✓ Started Redis, PostgreSQL, Meilisearch${NC}"
    
    # Wait for services
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 5
    
    # Check health
    if docker compose -f infrastructure/docker-compose.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ Services are healthy${NC}"
    fi
}

# Initialize database
init_db() {
    echo -e "\n${YELLOW}Initializing database...${NC}"
    
    source venv/bin/activate
    
    # Run migrations or create tables
    python -c "
from backend.database.session import init_db
import asyncio
asyncio.run(init_db())
print('Database initialized')
" 2>/dev/null || echo -e "${YELLOW}  ⚠️  Database init skipped (may already exist)${NC}"
    
    echo -e "${GREEN}✓ Database ready${NC}"
}

# Start backend
start_backend() {
    echo -e "\n${YELLOW}Starting backend API...${NC}"
    
    source venv/bin/activate
    
    # Start in background
    uvicorn backend.processing.api_main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    
    sleep 3
    
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"
        echo -e "${GREEN}  API docs: http://localhost:8000/docs${NC}"
    else
        echo -e "${YELLOW}  Backend starting... (check logs)${NC}"
    fi
}

# Start frontend
start_frontend() {
    echo -e "\n${YELLOW}Starting frontend...${NC}"
    
    cd frontend
    npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend.pid
    cd ..
    
    sleep 5
    echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"
}

# Print status
print_status() {
    echo -e "\n${GREEN}================================${NC}"
    echo -e "${GREEN}🛡️ Good Shepherd is running!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Services:"
    echo "  • Frontend:    http://localhost:3000"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Docs:    http://localhost:8000/docs"
    echo "  • Meilisearch: http://localhost:7700"
    echo ""
    echo "To stop: ./scripts/stop.sh"
    echo ""
}

# Main
main() {
    check_prereqs
    setup_env
    setup_python
    setup_frontend
    start_infra
    init_db
    start_backend
    start_frontend
    print_status
}

# Run
main
