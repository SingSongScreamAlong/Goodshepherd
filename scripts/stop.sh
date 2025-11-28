#!/bin/bash
# Stop Good Shepherd services

echo "🛑 Stopping Good Shepherd..."

# Stop frontend
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
    echo "✓ Stopped frontend"
fi

# Stop backend
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
    echo "✓ Stopped backend"
fi

# Stop infrastructure
cd infrastructure
docker compose down
cd ..

echo "✓ All services stopped"
