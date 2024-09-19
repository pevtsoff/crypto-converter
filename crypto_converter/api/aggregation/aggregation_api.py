from fastapi import APIRouter, Depends
from crypto_converter.api.aggregation.aggregation_service import AggregationService
from crypto_converter.common.models import BinanceTickerAggregationInfoResponse


aggregation_router = APIRouter(prefix="/aggregation", tags=["exchange"])


@aggregation_router.get(
    "/",
    response_model=BinanceTickerAggregationInfoResponse,
    response_model_by_alias=True,
)
async def get_aggregation_data(
    ticker_name: str,
    service: AggregationService = Depends(),
):
    return await service.get_aggregated_data(ticker_name)


@aggregation_router.get(
    "/view",
    response_model=BinanceTickerAggregationInfoResponse,
    response_model_by_alias=True,
)
async def get_aggregation_view_data(
    ticker_name: str,
    service: AggregationService = Depends(),
):
    return await service.get_aggregated_view_data(ticker_name)
