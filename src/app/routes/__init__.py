from fastapi import FastAPI
from fastapi.routing import APIRoute
from loguru import logger
from src.app.routes.auth_router import router as auth_router

routes = [auth_router]

def register_routes(app: FastAPI):
    for route in routes:
        app.include_router(route)

    routes_count = sum(len(route.routes) for route in routes)
    logger.info(f"Successfully registred {routes_count} API routes")