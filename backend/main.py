"""
TradeSense Backend API Server
Production-ready FastAPI application with modular architecture
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import uuid
import time
from datetime import datetime

# Core imports
from backend.core.config import settings
from backend.core.exceptions import TradeSenseException
from backend.core.response import ResponseHandler
from backend.db.connection import DatabaseManager, init_database

# API routers
from backend.api.v1 import api_v1_router
from backend.api.health.router import router as health_router

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"🚀 {settings.app_name} v{settings.version} starting up...")

    # Initialize database
    if not init_database():
        logger.error("Failed to initialize database")

    # Health check
    if DatabaseManager.health_check():
        logger.info("✅ Database connection healthy")
    else:
        logger.error("❌ Database connection failed")

    logger.info(f"✅ {settings.app_name} started successfully")
    yield

    # Shutdown
    logger.info(f"🛑 {settings.app_name} shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Authentication", 
            "description": "User authentication and authorization"
        },
        {
            "name": "Trades",
            "description": "Trade management and analytics"
        },
        {
            "name": "File Uploads",
            "description": "File upload and data processing"
        }
    ]
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Log request
    logger.info(f"Request {request_id}: {request.method} {request.url}")

    try:
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Request {request_id} completed in {process_time:.3f}s "
            f"with status {response.status_code}"
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request {request_id} failed in {process_time:.3f}s - Error: {str(e)}")
        raise


# Exception handlers
@app.exception_handler(TradeSenseException)
async def tradesense_exception_handler(request: Request, exc: TradeSenseException):
    """Handle custom TradeSense exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    error_response = ResponseHandler.error(
        error=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    error_response = ResponseHandler.error(
        error="HTTPException",
        message=exc.detail,
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    error_response = ResponseHandler.error(
        error="ValidationError",
        message="Invalid request data",
        details={"validation_errors": exc.errors()},
        request_id=request_id
    )

    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))

    logger.error(f"Unhandled exception in request {request_id}: {str(exc)}", exc_info=True)

    error_response = ResponseHandler.error(
        error=exc.__class__.__name__,
        message="Internal server error" if not settings.debug else str(exc),
        request_id=request_id
    )

    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


# Include routers
app.include_router(health_router)
app.include_router(api_v1_router)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint with API information"""
    return ResponseHandler.success(
        data={
            "name": settings.app_name,
            "version": settings.version,
            "description": settings.description,
            "docs_url": "/docs" if settings.debug else "Documentation disabled in production",
            "health_check": "/health"
        },
        message=f"Welcome to {settings.app_name} API"
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting {settings.app_name} server...")

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.debug
    )