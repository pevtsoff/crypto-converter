import pytest

from crypto_converter.database.db_models import BinanceTickerModel

@pytest.mark.asyncio
async def test_model_creation(setup_database, db_session):
    session = db_session
    ticker = BinanceTickerModel(
        ticker_name="btsusdt",
        price="1232134242",
        timestamp=2354646546,
    )
    session.add(ticker)
