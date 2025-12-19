from ..core.config import app_config
from ..api.routes import public, auth, protected

from starlette.concurrency import run_in_threadpool
from pyngrok.exception import PyngrokNgrokError
from contextlib import asynccontextmanager
from pyngrok import ngrok
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from dc_logger import get_logger

__all__ = ["app"]


logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    public_url = None
    if app_config.env != "production":
        try:
            listener = await run_in_threadpool(
                ngrok.connect,
                app_config.uvicorn_port,
                domain=app_config.public_domain,
            )
            public_url = listener.public_url
            await logger.info(f"ngrok tunnel established at {public_url}")
            print(f"Public URL: {public_url}")
        except PyngrokNgrokError as e:
            await logger.warning(f"Could not start ngrok tunnel: {e}")
            await logger.warning("Application will run without a public ngrok URL.")
            pass

    # yields to the running application
    yield

    if public_url:
        await run_in_threadpool(ngrok.disconnect, public_url)
        await logger.info("ngrok tunnel closed")


# Create the application instance
app = FastAPI(lifespan=lifespan)

# required to "remember" the user after they log in
app.add_middleware(SessionMiddleware, secret_key=app_config.starlette_session_key)

app.include_router(public.router, tags=["public"])
app.include_router(auth.router, tags=["auth"])
app.include_router(protected.router, tags=["protected"])