import uvicorn
from fastapi import APIRouter, Depends, FastAPI
from fastapi.encoders import decimal_encoder
from crypto_converter.common.exception_handlers import common_exception_handler
from crypto_converter.common.models import ExchangeBid, ExchangeResponse
from crypto_converter.exchange_api.exchange_service import ExchangeService

router = APIRouter(prefix="/exchange", tags=["exchange"])


@router.post("/", response_model=ExchangeResponse, response_model_by_alias=True)
async def exchange_currency(
    exchange_bid: ExchangeBid,
    service: ExchangeService = Depends(),
):
    data = await service.exchange(exchange_bid)
    return data


def create_fastapi_app():
    app = FastAPI(
        title="Crypto Converter",
        description="Converts the Crypto using Binance rates",
        version="1.0.0.",
        json_encode=decimal_encoder,
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
