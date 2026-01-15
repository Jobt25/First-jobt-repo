"""
app/main.py

Main FastAPI application for Jobt AI Career Coach.

Features:
- Authentication & authorization
- Interview practice sessions
- AI-powered feedback
- Subscription management
- Admin dashboard
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from .core.database import init_db, close_db, check_db_connection
# from app.core.middleware import setup_middleware
from .config import settings

# Import routers
from .routers.api.v1.auth_route import router as auth_router
from .routers.api.v1.categories_route import router as categories_router
from .routers.api.v1.interviews_route import router as interviews_router
from .routers.api.v1.feedback_route import router as feedback_router
from .routers.api.v1.analytics_route import router as analytics_router
from .routers.api.v1.admin_route import router as admin_router
# from app.routers.api.v1.users import router as users_router
# from app.routers.api.v1.subscriptions import router as subscriptions_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== LIFESPAN EVENTS ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Startup:
    - Initialize database
    - Check database connection
    - Log application start

    Shutdown:
    - Close database connections
    - Log application stop
    """
    # Startup
    logger.info("=" * 60)
    logger.info(" Starting Jobt AI Career Coach API")
    logger.info("=" * 60)

    try:
        # Initialize database
        await init_db()
        logger.info("✓ Database initialized")

        # Check connection
        if await check_db_connection():
            logger.info("✓ Database connection successful")
        else:
            logger.error("✗ Database connection failed")

        logger.info(f"✓ Environment: {settings.DEBUG and 'Development' or 'Production'}")
        logger.info(f"✓ API Version: {settings.VERSION}")
        logger.info(f"✓ Docs available at: http://localhost:{settings.PORT}/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info(" Shutting down Jobt AI Career Coach API")
    logger.info("=" * 60)

    try:
        await close_db()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}", exc_info=True)


# ==================== APPLICATION SETUP ====================

app = FastAPI(
    title="Jobt AI Career Coach API",
    description="""
    AI-powered interview practice and career coaching platform.

    ## Features
    -  Realistic interview simulations
    -  AI-powered feedback and analysis
    -  Progress tracking and analytics
    -  Industry-specific scenarios
    -  Subscription management

    ## Authentication
    All protected endpoints require a JWT token in the Authorization header:
    ```
    Authorization: Bearer <your_token>
    ```

    Get your token by registering or logging in via `/api/v1/auth/register` or `/api/v1/auth/login`.
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ==================== MIDDLEWARE ====================

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()

    # Log request
    logger.debug(
        f"→ {request.method} {request.url.path} "
        f"[Client: {request.client.host if request.client else 'unknown'}]"
    )

    # Process request
    try:
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.debug(
            f"← {request.method} {request.url.path} "
            f"[Status: {response.status_code}] "
            f"[Duration: {duration:.3f}s]"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(duration)

        return response

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"✗ {request.method} {request.url.path} "
            f"[Error: {str(e)}] "
            f"[Duration: {duration:.3f}s]",
            exc_info=True
        )
        raise


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


# ==================== INCLUDE ROUTERS ====================

# API v1 routes
api_v1_prefix = "/api/v1"

# Auth routes (ACTIVE)
app.include_router(auth_router, prefix=api_v1_prefix, tags=["Authentication"])
app.include_router(categories_router, prefix=api_v1_prefix, tags=["Job Categories"])
app.include_router(interviews_router, prefix=api_v1_prefix, tags=["Interviews"])
app.include_router(feedback_router, prefix=api_v1_prefix, tags=["Feedback"])
app.include_router(analytics_router, prefix=api_v1_prefix, tags=["Analytics"])
app.include_router(admin_router, prefix=api_v1_prefix, tags=["Admin"])

# User routes (TODO)
# app.include_router(users_router, prefix=api_v1_prefix, tags=["Users"])

# Subscription routes (TODO)
# app.include_router(subscriptions_router, prefix=api_v1_prefix, tags=["Subscriptions"])

# Admin routes (TODO)
# app.include_router(admin_router, prefix=api_v1_prefix, tags=["Admin"])


# ==================== ROOT ENDPOINTS ====================

@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint with basic information.
    """
    return {
        "message": "Welcome to Jobt AI Career Coach API",
        "version": settings.VERSION,
        "status": "operational",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "interviews": "/api/v1/interviews (coming soon)",
            "analytics": "/api/v1/analytics (coming soon)"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
    - status: Application status
    - database: Database connection status
    - timestamp: Current server time
    - version: API version
    """
    db_status = "connected" if await check_db_connection() else "disconnected"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.VERSION,
        "environment": "development" if settings.DEBUG else "production"
    }


@app.get("/ping", tags=["Health"])
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong"}


# ==================== STARTUP MESSAGE ====================

@app.get("/info", tags=["Info"])
async def info():
    """
    Get API information and available routes.
    """
    routes = []
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })

    return {
        "app_name": app.title,
        "version": settings.VERSION,
        "description": "AI-powered interview practice platform",
        "total_routes": len(routes),
        "available_routes": routes,
        "features": {
            "authentication": "✓ Active",
            "interviews": "⏳ Coming Soon",
            "feedback": "⏳ Coming Soon",
            "analytics": "⏳ Coming Soon",
            "subscriptions": "⏳ Coming Soon",
            "admin": "⏳ Coming Soon"
        }
    }


# ==================== CUSTOM MIDDLEWARE ====================

# Add any custom middleware here
# setup_middleware(app)


"""
First-jobt-repo/
├── users/                          
├── workbe/                          
├── manage.py
├── requirements.txt
"""