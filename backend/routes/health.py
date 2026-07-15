"""Health check endpoints."""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def health_status() -> Dict[str, Any]:
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BVRIT Chatbot API",
        "version": "1.0.0",
    }


@router.get("/readiness")
async def readiness() -> Dict[str, Any]:
    """Check if service is ready to accept traffic."""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/liveness")
async def liveness() -> Dict[str, Any]:
    """Check if service is alive."""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
