from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logger import logger
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.core.exceptions import register_exception_handlers
from app.modules.audit.routes import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name}...")

    yield

    logger.info(f"Stopping {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

register_exception_handlers(app)


@app.get("/", tags=["Root"])
async def root():
    return {"message": f"Welcome to {settings.app_name}"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(audit_router)
