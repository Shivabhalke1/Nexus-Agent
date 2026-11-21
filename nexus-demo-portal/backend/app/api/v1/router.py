"""Main API v1 router bundling all sub-routers."""
from fastapi import APIRouter
from app.api.v1.endpoints import health, products, auth, cart, orders, metrics, simulator

api_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_router.include_router(health.router)
api_router.include_router(products.router)
api_router.include_router(auth.router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(metrics.router)
api_router.include_router(simulator.router)
