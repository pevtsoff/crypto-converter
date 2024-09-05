from fastapi.responses import JSONResponse
from http import HTTPStatus
from fastapi import Request
from pydantic import ValidationError
from fastapi.encoders import jsonable_encoder
from crypto_converter.common.common import configure_logger
from crypto_converter.common.exceptions import NoValidTickerAvailableForTicker

logger = configure_logger(__name__)


async def common_exception_handler(request: Request, exc: Exception):
    logger.exception(exc)
    err_prefix = "Request failed: {}"
    if exc.__class__ == ValidationError:
        status_code = HTTPStatus.BAD_REQUEST
        msg = jsonable_encoder(exc.errors())
    elif exc.__class__ in (NoValidTickerAvailableForTicker,):
        status_code = HTTPStatus.SERVICE_UNAVAILABLE
        msg = err_prefix.format(exc)
    else:
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        msg = err_prefix.format(exc)

    return JSONResponse(
        status_code=status_code,
        content={"error": msg, "status_code": status_code},
    )
