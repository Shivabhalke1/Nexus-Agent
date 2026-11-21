"""
NEXUS OBSERVE - Unified Backend Gateway (Render & Cloud Deployment)
Runs all 3 backends (Demo Portal, Local Collector, Central SaaS) under a single port/URL.
"""

import os
import sys
import subprocess
import time
import asyncio
from typing import Optional
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Port assigned by Render or default to 8000
GATEWAY_PORT = int(os.environ.get("PORT", 8000))

# Internal microservice ports on loopback
DEMO_PORT = 8010
COLLECTOR_PORT = 8011
SAAS_PORT = 8012

app = FastAPI(
    title="NEXUS OBSERVE - Unified Cloud Gateway",
    description="Single-link unified gateway routing Demo Portal (:8010), Local Collector (:8011), and Central SaaS (:8012).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background processes
processes = []

def start_subprocesses():
    """Start all 3 backend services on internal ports."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    python_bin = sys.executable

    # 1. Demo Portal Backend (:8010)
    demo_dir = os.path.join(root_dir, "nexus-demo-portal", "backend")
    env_demo = os.environ.copy()
    env_demo["PORT"] = str(DEMO_PORT)
    p_demo = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(DEMO_PORT)],
        cwd=demo_dir,
        env=env_demo,
    )
    processes.append(("demo", p_demo))

    # 2. Local Collector Backend (:8011)
    collector_dir = os.path.join(root_dir, "nexus-local-collector", "collector")
    env_collector = os.environ.copy()
    env_collector["PORT"] = str(COLLECTOR_PORT)
    env_collector["DEMO_PORTAL_BASE_URL"] = f"http://127.0.0.1:{DEMO_PORT}"
    env_collector["CENTRAL_SAAS_URL"] = f"http://127.0.0.1:{SAAS_PORT}/api/v1/ingest"
    p_collector = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(COLLECTOR_PORT)],
        cwd=collector_dir,
        env=env_collector,
    )
    processes.append(("collector", p_collector))

    # 3. Central SaaS Backend (:8012)
    saas_dir = os.path.join(root_dir, "nexus-central-saas", "backend")
    env_saas = os.environ.copy()
    env_saas["PORT"] = str(SAAS_PORT)
    p_saas = subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(SAAS_PORT)],
        cwd=saas_dir,
        env=env_saas,
    )
    processes.append(("saas", p_saas))

    print(f"[NEXUS GATEWAY] All 3 microservices launched on ports {DEMO_PORT}, {COLLECTOR_PORT}, {SAAS_PORT}.")


@app.on_event("startup")
async def on_startup():
    start_subprocesses()


@app.on_event("shutdown")
def on_shutdown():
    for name, p in processes:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            p.kill()


# -------------------------------------------------------------------
# Reverse Proxy Helper
# -------------------------------------------------------------------
client = httpx.AsyncClient(timeout=30.0)

async def proxy_request(target_url: str, request: Request):
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    body = await request.body()
    try:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
            params=request.query_params,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
            media_type=resp.headers.get("content-type"),
        )
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={"error": "Bad Gateway", "target": target_url, "details": str(e)},
        )


# -------------------------------------------------------------------
# Service Routes
# -------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Health check endpoint for Render."""
    return {
        "status": "healthy",
        "gateway": "online",
        "services": {
            "demo_portal": f"http://127.0.0.1:{DEMO_PORT}",
            "local_collector": f"http://127.0.0.1:{COLLECTOR_PORT}",
            "central_saas": f"http://127.0.0.1:{SAAS_PORT}",
        },
    }


@app.get("/collector")
def redirect_collector():
    return Response(status_code=307, headers={"Location": "/collector/"})


@app.get("/saas")
def redirect_saas():
    return Response(status_code=307, headers={"Location": "/saas/"})


@app.api_route("/demo/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def route_demo(path: str, request: Request):
    return await proxy_request(f"http://127.0.0.1:{DEMO_PORT}/{path}", request)


@app.api_route("/collector/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def route_collector(path: str, request: Request):
    return await proxy_request(f"http://127.0.0.1:{COLLECTOR_PORT}/{path}", request)


@app.api_route("/saas/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def route_saas(path: str, request: Request):
    return await proxy_request(f"http://127.0.0.1:{SAAS_PORT}/{path}", request)


# Direct API smart router for frontends calling /api/v1/...
@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def route_smart_api(path: str, request: Request):
    referer = request.headers.get("referer", "")
    
    # 1. First check Referer to prioritize the originating UI
    if "/saas" in referer:
        return await proxy_request(f"http://127.0.0.1:{SAAS_PORT}/api/v1/{path}", request)
    if "/collector" in referer:
        return await proxy_request(f"http://127.0.0.1:{COLLECTOR_PORT}/api/v1/{path}", request)
    if "/demo" in referer or ":3000" in referer or "vercel.app" in referer:
        demo_endpoints = ("products", "cart", "checkout", "orders", "simulate")
        if any(path.startswith(ep) for ep in demo_endpoints):
            return await proxy_request(f"http://127.0.0.1:{DEMO_PORT}/api/v1/{path}", request)
    
    # 2. Path-based routing fallback
    collector_endpoints = ("approval/", "pipeline", "lab", "privacy", "audit", "killswitch", "adaptive", "redaction", "egress")
    if any(path.startswith(ep) for ep in collector_endpoints):
        return await proxy_request(f"http://127.0.0.1:{COLLECTOR_PORT}/api/v1/{path}", request)
    
    demo_endpoints = ("products", "cart", "checkout", "orders", "simulate")
    if any(path.startswith(ep) for ep in demo_endpoints):
        return await proxy_request(f"http://127.0.0.1:{DEMO_PORT}/api/v1/{path}", request)
        
    return await proxy_request(f"http://127.0.0.1:{SAAS_PORT}/api/v1/{path}", request)


# Direct API shortcuts for compatibility
@app.api_route("/api/v1/ingest", methods=["POST", "OPTIONS"])
async def route_direct_ingest(request: Request):
    return await proxy_request(f"http://127.0.0.1:{SAAS_PORT}/api/v1/ingest", request)


@app.api_route("/metrics", methods=["GET"])
async def route_direct_metrics(request: Request):
    return await proxy_request(f"http://127.0.0.1:{DEMO_PORT}/metrics", request)


@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    """Render root status page showing all 3 backends live."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEXUS OBSERVE - Unified Backend Gateway</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center p-6 font-sans">
        <div class="max-w-2xl w-full bg-slate-800/90 border border-slate-700 rounded-2xl p-8 space-y-6 shadow-2xl backdrop-blur">
            <div class="flex items-center justify-between pb-4 border-b border-slate-700">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white font-extrabold text-lg shadow-md">
                        ⚡
                    </div>
                    <div>
                        <h1 class="text-xl font-black text-white">NEXUS OBSERVE</h1>
                        <p class="text-xs text-slate-400">Unified Render Cloud Backend Gateway</p>
                    </div>
                </div>
                <span class="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    ● ALL 3 SERVICES ONLINE
                </span>
            </div>

            <p class="text-xs text-slate-300 leading-relaxed">
                Single-link backend gateway powering all 3 microservices on Render. Every API endpoint is active and reverse-proxied:
            </p>

            <div class="space-y-3">
                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 flex items-center justify-between">
                    <div>
                        <div class="text-sm font-bold text-white flex items-center gap-2">
                            <span>🛍️</span> 1. Demo Portal Backend
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono mt-0.5">Proxy Path: <code>/demo/api/v1/...</code></div>
                    </div>
                    <a href="/demo/api/v1/health" target="_blank" class="px-3 py-1.5 bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 text-xs font-bold rounded-lg border border-indigo-500/30 transition">
                        Check Health →
                    </a>
                </div>

                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 flex items-center justify-between">
                    <div>
                        <div class="text-sm font-bold text-white flex items-center gap-2">
                            <span>🛡️</span> 2. Local Privacy Collector
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono mt-0.5">Proxy Path: <code>/collector/api/v1/...</code></div>
                    </div>
                    <a href="/collector/api/v1/approval/pending" target="_blank" class="px-3 py-1.5 bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-300 text-xs font-bold rounded-lg border border-cyan-500/30 transition">
                        View Pending →
                    </a>
                </div>

                <div class="p-4 rounded-xl bg-slate-900/80 border border-slate-700/80 flex items-center justify-between">
                    <div>
                        <div class="text-sm font-bold text-white flex items-center gap-2">
                            <span>☁️</span> 3. Central SaaS Backend
                        </div>
                        <div class="text-[11px] text-slate-400 font-mono mt-0.5">Proxy Path: <code>/saas/api/v1/...</code></div>
                    </div>
                    <a href="/saas/api/v1/health/summary" target="_blank" class="px-3 py-1.5 bg-purple-600/30 hover:bg-purple-600/50 text-purple-300 text-xs font-bold rounded-lg border border-purple-500/30 transition">
                        Health Summary →
                    </a>
                </div>
            </div>

            <div class="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-700/80">
                <span>CICADA 2026 Hackathon</span>
                <a href="/health" class="hover:text-cyan-400 font-mono">Gateway Status JSON</a>
            </div>
        </div>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("unified_backend:app", host="0.0.0.0", port=GATEWAY_PORT, reload=False)
