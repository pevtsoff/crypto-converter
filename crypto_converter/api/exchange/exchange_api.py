from fastapi import APIRouter, Depends

from crypto_converter.common.models import ExchangeBid, ExchangeResponse
from crypto_converter.api.exchange.exchange_service import ExchangeService

exchange_router = APIRouter(prefix="/exchange", tags=["exchange"])


@exchange_router.post(
    "/", response_model=ExchangeResponse, response_model_by_alias=True
)
async def exchange_currency(
    exchange_bid: ExchangeBid,
    service: ExchangeService = Depends(),
):
    data = await service.exchange(exchange_bid)
    return data
