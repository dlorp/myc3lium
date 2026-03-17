"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import nodes, ws
from app.services.mesh_store import MeshStore

app = FastAPI(
    title="MYC3LIUM API",
    description="Backend for MYC3LIUM - Mycelial Network Visualization",
    version="0.1.0",
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mesh store and connect to WebSocket broadcasting
mesh_store = MeshStore()
ws.set_mesh_store(mesh_store)

# Make mesh_store available to routers
nodes.mesh_store = mesh_store

# Include routers
app.include_router(nodes.router)
app.include_router(ws.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MYC3LIUM API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
