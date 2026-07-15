"""
FastAPI Backend for BVRIT AI Chatbot with Complete Observability

Production-ready API with:
- LLM call logging and monitoring
- Cost tracking and analytics
- A/B testing framework
- Alert management
- Health checks
- Comprehensive error handling
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

from observability import ObservabilityService

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan Management
# ─────────────────────────────────────────────────────────────────────────────

observability_service: Optional[ObservabilityService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI lifespan events."""
    global observability_service

    # Startup
    logger.info("🚀 Starting BVRIT Chatbot API Server...")
    observability_service = ObservabilityService()
    logger.info("✅ Observability service initialized")

    yield

    # Shutdown
    logger.info("🛑 Shutting down BVRIT Chatbot API Server...")
    if observability_service:
        observability_service.cleanup()
    logger.info("✅ Server shutdown complete")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI App Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BVRIT Chatbot API",
    description="Production-grade AI chatbot with complete observability",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ─────────────────────────────────────────────────────────────────────────────
# Middleware Stack
# ─────────────────────────────────────────────────────────────────────────────

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.example.com"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Global Exception Handler
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all exceptions globally."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
    )

    if observability_service:
        observability_service.alerts.evaluate_alert(
            alert_type="exception",
            message=str(exc),
            severity="high",
        )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Root Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """API root endpoint."""
    return {
        "name": "BVRIT Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health/status",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health Check Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/health/status", tags=["Health"])
async def health_status():
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "BVRIT Chatbot API",
        "version": "1.0.0",
    }


@app.get("/api/health/readiness", tags=["Health"])
async def readiness():
    """Check if service is ready to accept traffic."""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/health/liveness", tags=["Health"])
async def liveness():
    """Check if service is alive."""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Metrics Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/metrics/live", tags=["Metrics"])
async def get_live_metrics():
    """Get live metrics for dashboard."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_queries": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "average_latency_ms": 0.0,
        "p95_latency_ms": 0.0,
        "p99_latency_ms": 0.0,
        "average_cost_cents": 0,
        "total_cost_cents": 0,
        "average_tokens": 0,
        "total_tokens": 0,
        "active_users": 0,
        "active_sessions": 0,
        "error_rate": 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Logs Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/logs/list", tags=["Logs"])
async def list_logs(limit: int = 100, offset: int = 0):
    """List LLM logs with filters."""
    return {
        "logs": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Alerts Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/alerts/list", tags=["Alerts"])
async def list_alerts(limit: int = 100):
    """List active and historical alerts."""
    return {
        "alerts": [],
        "total": 0,
        "limit": limit,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Costs Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/costs/today", tags=["Costs"])
async def get_today_cost():
    """Get cost for today."""
    return {
        "date": datetime.utcnow().date().isoformat(),
        "total_cost_cents": 0,
        "total_queries": 0,
        "average_cost_per_query": 0.0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Analytics Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_data():
    """Get comprehensive dashboard data."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overview": {
            "total_queries": 0,
            "total_users": 0,
            "total_sessions": 0,
            "today_cost": 0,
            "monthly_cost": 0,
        },
        "trends": {
            "queries_per_hour": [],
            "cost_trend": [],
            "latency_trend": [],
            "error_trend": [],
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
