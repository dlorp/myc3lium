"""FastAPI application entry point"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import messages, mesh, nodes, threads, ws
from app.services.live_data_source import LiveDataSource
from app.services.mesh_store import MeshStore
from app.services.mock_data import MockMeshDataSource
from app.services.reticulum_service import ReticulumBridge

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MYC3LIUM API",
    description="Backend for MYC3LIUM - Mycelial Network Visualization",
    version="0.2.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Reticulum bridge (gracefully no-ops on Mac)
reticulum = ReticulumBridge()
reticulum.start()

# Choose data source based on environment
if settings.use_live_data:
    logger.info("Using LiveDataSource (BATMAN + Reticulum)")
    data_source = LiveDataSource(use_live=True)
else:
    logger.info("Using MockDataSource (development mode)")
    data_source = MockMeshDataSource(seed=42)

# Initialize mesh store and connect to WebSocket broadcasting
mesh_store = MeshStore()
ws.set_mesh_store(mesh_store)

# Make mesh_store available to routers
nodes.mesh_store = mesh_store
messages.mesh_store = mesh_store
threads.mesh_store = mesh_store

# Make reticulum available to messages router
messages.reticulum = reticulum

# Make services available to mesh router
mesh.set_services(data_source, reticulum)

# Load initial data from chosen source
mesh_store.load_from_source(
    data_source.get_nodes(),
    data_source.get_threads(),
    data_source.get_messages(),
)

# Include routers
app.include_router(nodes.router)
app.include_router(messages.router)
app.include_router(threads.router)
app.include_router(ws.router)
app.include_router(mesh.router)


@app.on_event("startup")
async def start_mesh_monitor():
    """Start background mesh monitoring if live data is enabled."""
    if settings.use_live_data:
        logger.info("Starting mesh monitor (live data enabled)")
        ws.set_data_source(data_source)
        import asyncio

        asyncio.create_task(ws.mesh_monitor_loop())
    else:
        logger.info("Mesh monitor disabled (using mock data)")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MYC3LIUM API", "version": "0.2.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "live_data": settings.use_live_data,
        "reticulum": reticulum.available if reticulum else False,
    }
