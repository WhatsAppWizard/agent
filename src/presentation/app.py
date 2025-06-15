import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.config.container import container
from src.presentation.middleware.error_handler import ErrorHandlerMiddleware
from src.presentation.middleware.logging_middleware import LoggingMiddleware
from src.presentation.controllers import webhook_controller, health_controller

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting application...")
    try:
        await container.initialize()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await container.close()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Wizard Agent API",
        description="A conversational AI agent for WhatsApp with memory and context management",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware, exclude_paths=["/health", "/docs", "/openapi.json"])
    app.add_middleware(ErrorHandlerMiddleware, exclude_paths=["/health", "/docs", "/openapi.json"])
    
    # Include routers
    app.include_router(health_controller.router)
    app.include_router(webhook_controller.router)
    
    return app

# Create the application instance
app = create_app() 