#!/usr/bin/env bash
# One-click startup script for NEXUS Demo Portal local development
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=========================================================="
echo " Starting NEXUS Demo Portal (Local Dev Mode)"
echo "=========================================================="

# 1. Start Backend in background
echo "[1/3] Starting Backend API Server on port 8000..."
cd "${ROOT_DIR}/backend"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for Backend health check..."
sleep 2
until curl -s http://localhost:8000/api/v1/health > /dev/null; do
  sleep 1
done
echo "✓ Backend API is HEALTHY on http://localhost:8000"

# 2. Start Frontend in background
echo "[2/3] Starting Next.js Frontend on port 3000..."
cd "${ROOT_DIR}/frontend"
npm run dev &
FRONTEND_PID=$!

echo "=========================================================="
echo " NEXUS Demo Portal is RUNNING!"
echo "   - Frontend UI:        http://localhost:3000"
echo "   - Failure Simulator:  http://localhost:3000/simulator"
echo "   - Backend API Docs:   http://localhost:8000/docs"
echo "   - Prometheus Scraper: http://localhost:8000/metrics"
echo "   - Health Check:       http://localhost:8000/api/v1/health"
echo "=========================================================="
echo "Press CTRL+C to stop all servers."

trap "kill ${BACKEND_PID} ${FRONTEND_PID} 2>/dev/null || true; exit" SIGINT SIGTERM
wait
