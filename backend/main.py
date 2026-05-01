"""
Smart Business Management & Tracking System - Main Application
FastAPI Backend Server
"""

from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from app.routers import auth, sales, inventory, employees, analytics, receipt, seed, audit
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hooks for startup/shutdown."""
    yield


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

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(receipt.router, prefix="/api/receipts", tags=["Receipt Processing"])
app.include_router(audit.router, tags=["Audit Logs"])
app.include_router(seed.router, prefix="/api", tags=["Database"])


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
