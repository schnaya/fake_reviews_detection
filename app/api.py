from pathlib import Path

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from common_lib.models import User
from common_lib.services.auth.auth_service import get_current_active_user
from routes.comment import comment_router
from routes.product import product_router
from common_lib.services.rm.rm import connect_rabbitmq, close_rabbitmq
from routes.user import user_route
from common_lib.database.database import init_db
from common_lib.database.config import get_settings
from core.templating import templates

import uvicorn
import logging
APP_DIR = Path(__file__).parent

logger = logging.getLogger(__name__)
settings = get_settings()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.API_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc"
    )
    app.mount(
        "/static",
        StaticFiles(directory=str(APP_DIR / "view/static")),
        name="static"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(user_route, prefix="/api/auth", tags=["Authentication"])
    app.include_router(product_router, prefix="/api/products", tags=["Products"])
    app.include_router(comment_router, prefix="/api/comments", tags=["Comments"])
    return app


app = create_application()


@app.on_event("startup")
async def on_startup():
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Connecting to RabbitMQ...")
        await connect_rabbitmq()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise


@app.get("/", response_class=HTMLResponse, summary="Главная страница")
async def get_home_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Serves the main page listing all products."""
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})


@app.get("/login", response_class=HTMLResponse, summary="Страница входа")
async def get_login_page(request: Request):
    """Serves the login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse, summary="Страница регистрации")
async def get_register_page(request: Request):
    """Serves the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/products/{product_id}", response_class=HTMLResponse, summary="Страница продукта")
async def get_product_page(request: Request, product_id: str, current_user: User = Depends(get_current_active_user)):
    """Serves the product detail page."""
    return templates.TemplateResponse("product_detail.html", {"request": request, "product_id": product_id,
                                                              "current_user": current_user})


@app.get("/create-product", response_class=HTMLResponse, summary="Страница создания продукта")
async def get_create_product_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Serves the page for creating a new product."""
    return templates.TemplateResponse("create_product.html", {"request": request, "current_user": current_user})


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    await close_rabbitmq()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(
        'api:app',
        host='0.0.0.0',
        port=8080,
        reload=True,
        log_level="info"
    )