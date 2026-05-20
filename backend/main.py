"""
Smart Business Management & Tracking System - Main Application
FastAPI Backend Server
"""

from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import uuid
import time
import logging

from app.routers import auth, sales, inventory, employees, analytics, receipt, seed, audit, organizations
from app.core.config import settings

# Configure application logger
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Prevent duplicate handler setup
if not logger.handlers:
    import os
    from logging.handlers import RotatingFileHandler
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    app_handler.setFormatter(app_formatter)
    logger.addHandler(app_handler)
    logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hooks for startup/shutdown."""
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")


app = FastAPI(
    title="Smart Business Management & Tracking System",
    description="Comprehensive business platform with sales, inventory, and employee management",
    version="1.0.0",
    lifespan=lifespan
)

# Exception handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_type = error.get("type", "unknown")
        errors.append({
            "field": field,
            "message": msg,
            "type": error_type
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": errors,
            "message": "Validation error: Please check the required fields"
        }
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request audit and correlation middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """
    Centralized request middleware that:
    1. Adds X-Correlation-ID to every response for request tracing (ISO 27001 A.12.4.3)
    2. Logs all requests with timing for performance monitoring
    3. Tracks error responses for operational monitoring
    """
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Store correlation ID in request state for downstream use
    request.state.correlation_id = correlation_id
    
    # Record start time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Time-Ms"] = str(round(duration_ms, 2))
        
        # Log slow requests (>2s) for performance monitoring
        if duration_ms > 2000:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.url.path} "
                f"took {duration_ms:.0f}ms [correlation: {correlation_id}]"
            )
        
        # Log server errors (5xx) for operational awareness
        if response.status_code >= 500:
            logger.error(
                f"SERVER ERROR: {request.method} {request.url.path} "
                f"returned {response.status_code} [correlation: {correlation_id}]"
            )
        
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(
            f"UNHANDLED EXCEPTION: {request.method} {request.url.path} "
            f"failed after {duration_ms:.0f}ms: {str(e)} [correlation: {correlation_id}]"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "correlation_id": correlation_id}
        )


# Trusted host middleware to prevent Host header attacks
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "0.0.0.0", "*.localhost", "frontend", "backend"]
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(receipt.router, prefix="/api/receipts", tags=["Receipt Processing"])
app.include_router(audit.router, tags=["Audit Logs"])
app.include_router(seed.router, prefix="/api", tags=["Database"])
app.include_router(organizations.router, prefix="/api/organizations", tags=["Organizations"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Business Management & Tracking System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from app.database import test_postgres_connection, test_mongodb_connection
    
    postgres_ok, postgres_msg = test_postgres_connection()
    mongodb_ok, mongodb_msg = test_mongodb_connection()
    
    status = "healthy" if postgres_ok else "unhealthy"
    
    return {
        "status": status,
        "postgresql": {
            "connected": postgres_ok,
            "message": postgres_msg
        },
        "mongodb": {
            "connected": mongodb_ok,
            "message": mongodb_msg
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
