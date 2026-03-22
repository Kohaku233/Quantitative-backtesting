from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.api import router as api_router
from backend.app.config import get_settings
from backend.app.models.backtests import build_error_envelope


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,  # noqa: ARG001
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=build_error_envelope(
                code="invalid_request",
                message="Request validation failed.",
                details={"errors": jsonable_encoder(exc.errors())},
            ).model_dump(),
        )

    return app


app = create_app()
