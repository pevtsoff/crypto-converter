from fastapi import FastAPI
from fastapi.encoders import decimal_encoder

from crypto_converter.api.aggregation.aggregation_api import aggregation_router
from crypto_converter.common import settings
from crypto_converter.common.exception_handlers import common_exception_handler
import uvicorn

from crypto_converter.api.exchange.exchange_api import exchange_router


def create_fastapi_app():
    app = FastAPI(
        title="Crypto Converter",
        description="Converts the Crypto using Binance rates",
        version="1.0.0.",
        json_encode=decimal_encoder,
    )
    app.include_router(exchange_router)
    app.include_router(aggregation_router)
    app.add_exception_handler(Exception, common_exception_handler)
    return app


def start_exchange_api():
    app = create_fastapi_app()
    app.json_encoder = decimal_encoder
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEV_MODE,
        workers=settings.UVICORN_WORKERS,
    )


if __name__ == "__main__":
    start_exchange_api()
