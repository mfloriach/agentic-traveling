from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize shared resources here.
    yield
    # Shutdown: close clients here.


def create_app() -> FastAPI:
    app = FastAPI(
        title="RAG API",
        lifespan=lifespan,
    )

    app.include_router(router, prefix="/api")

    return app


app = create_app()