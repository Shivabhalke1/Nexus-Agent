#!/usr/bin/env bash
# ==============================================================================
# NEXUS Central SaaS Startup Script (Port 8002)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAAS_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${SAAS_ROOT}/backend"
VENV_PATH="/Volumes/SHIV BHALKE/NEXUS-OBSERVE/nexus-demo-portal/backend/.venv"

echo "=============================================================================="
echo " Starting NEXUS Central SaaS"
echo " Service Port: 8002"
echo " Dashboard UI: http://localhost:8002"
echo " API Docs:    http://localhost:8002/docs"
echo "=============================================================================="

if [ -f "${VENV_PATH}/bin/activate" ]; then
    echo "Activating virtualenv: ${VENV_PATH}"
    source "${VENV_PATH}/bin/activate"
else
    echo "Using default python3 environment"
fi

cd "${BACKEND_DIR}"
export PYTHONPATH="${BACKEND_DIR}"
export PORT=8002
export HOST="0.0.0.0"

exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
