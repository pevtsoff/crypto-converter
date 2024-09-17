import time
import pytest
from unittest.mock import AsyncMock, patch
from deepdiff import DeepDiff
from crypto_converter.common.models import BinanceTicker
from crypto_converter.exchange_api.exchange_api import create_fastapi_app

app = create_fastapi_app()

ticker_obj = BinanceTicker(
    ticker_name="btsusdt", price="43192.111223345675", timestamp=int(time.time())
)


async def get_ticker_from_redis_mock(*args, **kwargs) -> BinanceTicker:
    return ticker_obj


@pytest.fixture
def redis_mock():
    with patch("redis.asyncio.StrictRedis.ping", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_json,expected_json",
    [
        (
            {"from": "btc", "to": "usdt", "amount_from": 1},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "1",
                "amount_to": "43192.111223usdt",
                "rate_timestamp": 1706769690,
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_from": 0.110002},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "0.110002",
                "amount_to": "4751.21861875usdt",
                "rate_timestamp": 1706769690,
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_from": 1200},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "1200",
                "amount_to": "51830533.4676usdt",
                "rate_timestamp": 1706769690,
            },
        ),
        # amount_to tests
        (
            {"from": "btc", "to": "usdt", "amount_to": 1000.0},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "0.023152376017btc",
                "amount_to": "1000",
                "rate_timestamp": 1706769690,
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_to": 1},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "0.000023152376btc",
                "amount_to": "1",
                "rate_timestamp": 1706769690,
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_to": 10000000},
            {
                "from": "btc",
                "to": "usdt",
                "ticker_name": "btcusdt",
                "ticker_price": ticker_obj.price,
                "amount_from": "231.523760169btc",
                "amount_to": "10000000",
                "rate_timestamp": 1706769690,
            },
        ),
    ],
)
def test_conversion_from(client, input_json, expected_json, redis_mock):
    with patch(
        "crypto_converter.exchange_api.exchange_service.ExchangeService.get_ticker_from_redis",
        side_effect=get_ticker_from_redis_mock,
    ):
        response = client.post("/exchange", json=input_json)

        resp_json = response.json()
        diff = DeepDiff(expected_json, resp_json, exclude_paths=["rate_timestamp"])

        assert response.status_code == 200, resp_json
        assert diff == {}


# negative tests
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "input_json,expected_json",
    [
        (
            {"from": "btc", "to": "usdt", "amount_from": 0.1111111},
            {
                "detail": [
                    {
                        "type": "decimal_max_places",
                        "loc": ["body", "amount_from"],
                        "msg": "Decimal input should have no more than 6 decimal places",
                        "input": 0.1111111,
                        "ctx": {"decimal_places": 6},
                        "url": "https://errors.pydantic.dev/2.8/v/decimal_max_places",
                    }
                ]
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_from": 0},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, amount_from or amount_to should be passed",
                        "input": {"from": "btc", "to": "usdt", "amount_from": 0},
                        "ctx": {"error": {}},
                        "url": "https://errors.pydantic.dev/2.8/v/value_error",
                    }
                ]
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_to": 0.1111111},
            {
                "detail": [
                    {
                        "type": "decimal_max_places",
                        "loc": ["body", "amount_to"],
                        "msg": "Decimal input should have no more than 6 decimal places",
                        "input": 0.1111111,
                        "ctx": {"decimal_places": 6},
                        "url": "https://errors.pydantic.dev/2.8/v/decimal_max_places",
                    }
                ]
            },
        ),
        (
            {"from": "btc", "to": "usdt", "amount_to": 0},
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body"],
                        "msg": "Value error, amount_from or amount_to should be passed",
                        "input": {"from": "btc", "to": "usdt", "amount_to": 0},
                        "ctx": {"error": {}},
                        "url": "https://errors.pydantic.dev/2.8/v/value_error",
                    }
                ]
            },
        ),
    ],
)
def test_conversion_from_negative(client, input_json, expected_json, redis_mock):
    with patch(
        "crypto_converter.exchange_api.exchange_service.ExchangeService.get_ticker_from_redis",
        side_effect=get_ticker_from_redis_mock,
    ):
        response = client.post("/exchange", json=input_json)

        resp_json = response.json()
        diff = DeepDiff(expected_json, resp_json, exclude_paths=["rate_timestamp"])

        assert response.status_code == 422, resp_json
        assert diff == {}
