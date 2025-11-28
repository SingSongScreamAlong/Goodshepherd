#!/bin/bash
# Good Shepherd Development Mode (No Docker Required)
# Uses SQLite instead of PostgreSQL, in-memory cache instead of Redis

set -e

echo "🛡️ Good Shepherd - Development Mode"
echo "===================================="
echo "Running without Docker (SQLite + in-memory)"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Setup Python environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q --upgrade pip

echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q -r requirements.txt

# Create data directory
mkdir -p data

# Export dev mode environment
export DEV_MODE=true
export REDIS_URL=""
export MEILISEARCH_URL=""
export LOG_LEVEL=INFO

# Initialize database
echo -e "${YELLOW}Initializing SQLite database...${NC}"
python -c "
import asyncio
from backend.database.session import init_database
asyncio.run(init_database())
print('Database initialized at ./data/goodshepherd.db')
"

# Start backend in background
echo -e "${YELLOW}Starting backend API...${NC}"
uvicorn backend.processing.api_main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo $BACKEND_PID > .backend.pid

sleep 3

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"
else
    echo -e "${YELLOW}Backend starting... (may take a moment)${NC}"
fi

# Setup and start frontend
echo -e "${YELLOW}Setting up frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    npm install
fi

echo -e "${YELLOW}Starting frontend...${NC}"
REACT_APP_API_BASE=http://localhost:8000 npm start &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../.frontend.pid

cd ..

echo ""
echo -e "${GREEN}===================================${NC}"
echo -e "${GREEN}🛡️ Good Shepherd Dev Mode Running${NC}"
echo -e "${GREEN}===================================${NC}"
echo ""
echo "Services:"
echo "  • Frontend:     http://localhost:3000"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/docs"
echo ""
echo "Routes:"
echo "  • /mobile   - Mobile Dashboard"
echo "  • /checkin  - Safety Check-in"
echo "  • /analyst  - Analyst Dashboard"
echo "  • /dashboard - Main Dashboard"
echo ""
echo "Database: ./data/goodshepherd.db (SQLite)"
echo ""
echo "Press Ctrl+C to stop, or run: ./scripts/stop.sh"
echo ""

# Wait for Ctrl+C
wait
