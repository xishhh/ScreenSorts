from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
)
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ScreenSorts API")
    logger.info(f"Debug mode: {settings.app_debug}")

    from app.services.demo_mode_service import DemoModeService

    demo = DemoModeService()
    status = demo.check_readiness()
    if status.ready:
        logger.info(
            "Demo Mode READY — %d screenshots across %d datasets",
            status.screenshot_count,
            status.dataset_count,
        )
    else:
        logger.warning("Demo Mode NOT READY")
        for component in [status.corpus, status.ocr, status.embeddings, status.index]:
            if not component.exists:
                logger.warning("  Missing: %s — %s", component.name, component.details)
        logger.warning("Run 'python -m app.scripts.build_demo_corpus' to rebuild the demo corpus")

    yield
    logger.info("Shutting down ScreenSorts API")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(v1_router)

data_dir = settings._resolve("data")
if data_dir.is_dir():
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")
    logger.info("Serving static files from %s at /data", data_dir)
