import logging

from fastapi import FastAPI

from api.deterministic_behavior_api import router as deterministic_behavior_router


logger = logging.getLogger(__name__)


def register_behavior_routes(app: FastAPI) -> None:
    app.include_router(deterministic_behavior_router, prefix="/api")
    logger.info("behavior router registered prefix=/api")
