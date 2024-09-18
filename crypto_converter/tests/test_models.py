import pytest
from crypto_converter.database.db_models import (
    BinanceTickersModel,
    BinanceTickerDataModel,
)


@pytest.mark.asyncio
async def test_model_creation(db_session):
    session = db_session
    ticker = BinanceTickersModel(
        ticker_name="btsusdt",
    )
    ticker_data = BinanceTickerDataModel(
        price="1232134242", timestamp=2354646546, json_data="{}"
    )
    ticker.ticker_data.append(ticker_data)
    session.add(ticker)
