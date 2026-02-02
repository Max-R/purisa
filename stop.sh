#!/bin/bash

# Purisa Stop Script
# Stops all running Purisa servers

echo "Stopping Purisa servers..."

# Kill backend
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null && echo "Backend stopped (PID: $BACKEND_PID)" || echo "Backend not running"
    rm .backend.pid
fi

# Kill frontend
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null && echo "Frontend stopped (PID: $FRONTEND_PID)" || echo "Frontend not running"
    rm .frontend.pid
fi

# Kill tailwind watcher
if [ -f .tailwind.pid ]; then
    TAILWIND_PID=$(cat .tailwind.pid)
    kill $TAILWIND_PID 2>/dev/null && echo "Tailwind watcher stopped (PID: $TAILWIND_PID)" || true
    rm .tailwind.pid
fi

# Also kill any lingering uvicorn, bun, or tailwind processes
pkill -f "uvicorn purisa.main:app" 2>/dev/null || true
pkill -f "bun index.html" 2>/dev/null || true
pkill -f "tailwindcss.*watch" 2>/dev/null || true

echo "All Purisa servers stopped"
