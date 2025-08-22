from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn
from .core.config import settings
from .routers import sessions_router, websocket_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Memento Box API - Complex logic processing (AI, CIST evaluation, reports). Basic CRUD operations are handled directly via Supabase.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.debug else None
            }
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "success": True,
        "message": "Memento Box API is running",
        "data": {
            "status": "healthy",
            "environment": settings.environment
        }
    }


# Root endpoint
@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Welcome to Memento Box API",
        "data": {
            "version": "1.0.0",
            "docs_url": "/docs",
            "health_check": "/health"
        }
    }


# Include routers with API prefix
API_V1_PREFIX = "/api/v1"

# Include complex logic routers
app.include_router(sessions_router, prefix=API_V1_PREFIX)
app.include_router(websocket_router, prefix=API_V1_PREFIX)

# Note: Auth, users, photos routers removed - using Supabase directly from frontend


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )