import pytest
from crypto_converter.database.db_models import (
    BinanceTickersModel,
    BinanceTickerDataModel,
)
from sqlalchemy import select


@pytest.mark.asyncio
async def test_model_creation(db_engine, db_session_2, event_loop):
    session = db_session_2
    # test data
    test_ticker_name = "btcusdt"
    test_price = "1232134242"
    test_timestamp = 2354646546

    ticker = BinanceTickersModel(
        ticker_name=test_ticker_name,
    )
    ticker_data = BinanceTickerDataModel(
        price=test_price, timestamp=test_timestamp, json_data="{}"
    )

    ticker.ticker_data.append(ticker_data)
    session.add(ticker)

    await session.commit()

    # Getting saved actual ticker and its data
    stmt = select(BinanceTickersModel).where(
        BinanceTickersModel.ticker_name == test_ticker_name,
    )
    result = await session.execute(stmt)
    actual_ticker = result.scalars().first()

    assert actual_ticker.id is not None
    assert actual_ticker.ticker_data[0] == ticker_data
