import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, APIRouter, Depends
from fastapi.encoders import decimal_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_converter.db import sessionmanager, get_db_session
from crypto_converter.exchange_service import ExchangeService
from crypto_converter.exception_handlers import common_exception_handler
from crypto_converter.models import ExchangeResponse, ExchangeBid


exchange_api_host = os.getenv("EXCHANGE_API_HOST", "0.0.0.0")
exchange_api_port = os.getenv("EXCHANGE_API_PORT", 8000)
router = APIRouter(prefix="/exchange", tags=["exchange"])


@router.post("/", response_model=ExchangeResponse, response_model_by_alias=True)
async def exchange_currency(
    exchange_bid: ExchangeBid,
    service: ExchangeService = Depends(),
    #db_session: AsyncIterator[AsyncSession] = Depends(get_db_session)
):
    data = await service.exchange(exchange_bid)
    return data



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


def create_fastapi_app():
    app = FastAPI(
        title="Crypto Converter",
        description="Converts the Crypto using Binance rates",
        version="1.0.0.",
        json_encode=decimal_encoder,
        lifespan=lifespan
    )
    app.include_router(router)
    app.add_exception_handler(Exception, common_exception_handler)
    return app


def start_exchange_api():
    app = create_fastapi_app()
    app.json_encoder = decimal_encoder
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    start_exchange_api()
