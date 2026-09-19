from fastapi import FastAPI
from loguru import logger

from src.app.routes.auth_router import router as auth_router
from src.app.routes.session_router import router as session_router

routes = [auth_router, session_router]


def register_routes(app: FastAPI):
    for route in routes:
        app.include_router(route)

    routes_count = sum(len(route.routes) for route in routes)
    logger.info(f"Successfully registred {routes_count} API routes")
