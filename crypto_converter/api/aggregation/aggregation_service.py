from sqlalchemy.orm import joinedload
from crypto_converter.common.models import (
    BinanceTickerAggregationInfoResponse,
)
from crypto_converter.database.db import get_db_session
from crypto_converter.database.db_models import BinanceTickerAggregatedData
from sqlalchemy import select, text


class AggregationService:
    async def get_aggregated_data(
        self, ticker_name: str
    ) -> BinanceTickerAggregationInfoResponse:
        async with get_db_session() as session:
            stmt = (
                select(BinanceTickerAggregatedData)
                .options(joinedload(BinanceTickerAggregatedData.ticker))
                .where(BinanceTickerAggregatedData.ticker.has(ticker_name=ticker_name))
            )
            result = await session.execute(stmt)
            agg_data = result.scalars().first()

        return BinanceTickerAggregationInfoResponse(
            ticker_name=agg_data.ticker.ticker_name,
            min_price=agg_data.min_price,
            max_price=agg_data.max_price,
            avg_price=agg_data.avg_price,
            timestamp=agg_data.created_at,
        )

    async def get_aggregated_view_data(
        self, ticker_name: str
    ) -> BinanceTickerAggregationInfoResponse:
        async with get_db_session() as session:
            stmt = text(
                """
                SELECT *
                FROM aggregated_binance_prices
                JOIN binance_tickers_list
                    ON aggregated_binance_prices.ticker_id = binance_tickers_list.id
                WHERE binance_tickers_list.ticker_name = :ticker_name
            """
            ).bindparams(ticker_name=ticker_name)
            result = await session.execute(stmt)
            agg_data = result.fetchone()  # Use fetchone() to get a single result

        if agg_data:
            return BinanceTickerAggregationInfoResponse(
                ticker_name=agg_data.ticker_name,
                min_price=agg_data.min_price,
                max_price=agg_data.max_price,
                avg_price=agg_data.avg_price,
                timestamp=agg_data.created_at,
            )
        else:
            raise ValueError("No data found for the specified ticker.")
