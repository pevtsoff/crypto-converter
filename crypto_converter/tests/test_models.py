import pytest
from crypto_converter.database.db_models import (
    BinanceTickersModel,
    BinanceTickerDataModel,
)
from sqlalchemy import select


@pytest.mark.asyncio
async def test_model_creation(db_engine, db_session_2, event_loop):
    session = db_session_2
    ticker = BinanceTickersModel(
        ticker_name="btcusdt",
    )
    ticker_data = BinanceTickerDataModel(
        price="1232134242", timestamp=2354646546, json_data="{}"
    )
    ticker.ticker_data.append(ticker_data)
    session.add(ticker)
    session.add(ticker_data)
    await session.commit()
    stmt = select(BinanceTickersModel).where(
        BinanceTickersModel.ticker_name == "btcusdt"
    )
    result = await session.execute(stmt)
    t = result.scalars().first()
    assert t is not None
