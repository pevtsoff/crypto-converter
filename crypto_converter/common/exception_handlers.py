from typing import Any
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette import status
from crypto_converter.common.common import configure_logger
from crypto_converter.common.models import DetailMessage, ErrorResponse

logger = configure_logger(__name__)


async def common_exception_handler(request: Request, exc: Any) -> JSONResponse:
    logger.exception(exc)

    status_code: int = status.HTTP_400_BAD_REQUEST
    msg: Any = None

    match exc:
        case RequestValidationError():
            msg = DetailMessage(
                errors=exc.errors(), body=exc.body, status_code=status_code
            )

        case StarletteHTTPException():
            msg = DetailMessage(errors=str(exc.detail), status_code=exc.status_code)
            status_code = int(exc.status_code)

        case _:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            msg = DetailMessage(
                errors="Internal Server Error.", status_code=status_code
            )

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(ErrorResponse(detail=msg).model_dump()),
    )
