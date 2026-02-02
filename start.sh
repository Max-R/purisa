#!/bin/bash

# Purisa Startup Script
# Starts backend API server and frontend dev server

set -e  # Exit on error

echo "Starting Purisa Coordination Detection System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if database exists, if not initialize it
if [ ! -f "purisa.db" ]; then
    echo -e "${YELLOW}Database not found. Initializing...${NC}"
    source backend/venv/bin/activate
    python3 cli.py init
    deactivate
    echo ""
fi

# Start backend server
echo -e "${BLUE}Starting Backend API Server...${NC}"
cd backend
source venv/bin/activate
python3 -m uvicorn purisa.main:app --reload &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}Backend running on http://localhost:8000 (PID: $BACKEND_PID)${NC}"
echo ""

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo -e "${BLUE}Starting Frontend Dev Server...${NC}"
cd frontend

# Use Bun's native dev server
if command -v bun &> /dev/null; then
    # Build Tailwind CSS first
    bunx tailwindcss -i ./src/style.css -o ./src/output.css --minify 2>/dev/null
    # Start Tailwind in watch mode (background)
    bunx tailwindcss -i ./src/style.css -o ./src/output.css --watch 2>/dev/null &
    TAILWIND_PID=$!
    bun index.html &
    FRONTEND_PID=$!
else
    echo -e "${YELLOW}Bun not found. Please install Bun to run the frontend.${NC}"
    cd ..
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

cd ..
echo -e "${GREEN}Frontend running on http://localhost:3000 (PID: $FRONTEND_PID)${NC}"
echo ""

echo -e "${GREEN}----------------------------------------------${NC}"
echo -e "${GREEN}Purisa is running!${NC}"
echo ""
echo -e "  Backend API:  ${BLUE}http://localhost:8000${NC}"
echo -e "  API Docs:     ${BLUE}http://localhost:8000/docs${NC}"
echo -e "  Dashboard:    ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo -e "${GREEN}----------------------------------------------${NC}"

# Store PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid
echo $TAILWIND_PID > .tailwind.pid

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping servers...${NC}"

    if [ -f .backend.pid ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm .backend.pid
        echo -e "${GREEN}Backend stopped${NC}"
    fi

    if [ -f .frontend.pid ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm .frontend.pid
        echo -e "${GREEN}Frontend stopped${NC}"
    fi

    if [ -f .tailwind.pid ]; then
        TAILWIND_PID=$(cat .tailwind.pid)
        kill $TAILWIND_PID 2>/dev/null || true
        rm .tailwind.pid
    fi

    echo -e "${GREEN}Purisa stopped${NC}"
    exit 0
}

# Set trap to catch Ctrl+C
trap cleanup INT TERM

# Wait for user to stop
wait
