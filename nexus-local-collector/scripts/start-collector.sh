#!/bin/bash
# NEXUS Local Collector Startup Script
# CICADA 2026 - NEXUS OBSERVE

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$DIR/.." && pwd )"
COLLECTOR_DIR="$PROJECT_ROOT/collector"

echo "============================================================"
echo " Starting NEXUS Local Collector (Port 8001)"
echo " Environment: Local Customer Privacy Boundary"
echo "============================================================"

# Detect Python virtualenv
if [ -d "$PROJECT_ROOT/../nexus-demo-portal/backend/.venv" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/../nexus-demo-portal/backend/.venv/bin/python"
    UVICORN_EXEC="$PROJECT_ROOT/../nexus-demo-portal/backend/.venv/bin/uvicorn"
elif [ -d "$COLLECTOR_DIR/.venv" ]; then
    PYTHON_EXEC="$COLLECTOR_DIR/.venv/bin/python"
    UVICORN_EXEC="$COLLECTOR_DIR/.venv/bin/uvicorn"
else
    PYTHON_EXEC="python3"
    UVICORN_EXEC="uvicorn"
fi

cd "$COLLECTOR_DIR"
export PYTHONPATH=.

echo "Using Python executable: $PYTHON_EXEC"
echo "Serving Approval Dashboard on http://localhost:8001/ui"
echo "Health Endpoint: http://localhost:8001/health"

exec $UVICORN_EXEC app.main:app --host 0.0.0.0 --port 8001
