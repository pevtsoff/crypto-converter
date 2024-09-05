import asyncio
import os
import sys
import time
from copy import deepcopy
from typing import AsyncIterator

from dotenv import load_dotenv
import websockets
import json

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_converter.common import configure_logger, repeat, connect_to_redis
from crypto_converter.db import get_db_session
from crypto_converter.models import BinanceTicker
from crypto_converter.db_models import BinanceTickerModel


load_dotenv()
logger = configure_logger(__name__)

redis_flush_timeout = int(os.getenv("REDIS_FLUSH_TIMEOUT", 30))
redis_expiry_time = int(os.getenv("REDIS_EXPIRY_TIME", 3600))

binance_stream_name = os.getenv("BINANCE_STREAM_NAME", "")
binance_stream_base_url = os.getenv(
    "BINANCE_STREAM_BASE_URL", "wss://stream.binance.com:9443/stream?streams="
)
binance_stream_url = binance_stream_base_url + binance_stream_name

tickers = {}


async def process_msg(message):
    try:
        data = json.loads(message)

    except json.decoder.JSONDecodeError as e:
        logger.exception("unable to decode msg '%s', error: %s", message, e)

    else:
        if "data" in data:
            ticker_data = data["data"]

            for ticker in ticker_data:
                symbol = ticker["s"].lower()
                price = ticker["c"]
                event_time = ticker["E"]
                tickers[symbol] = BinanceTicker(
                    **{"ticker_name":symbol, "price": price, "timestamp": event_time}
                ).model_dump()

            logger.warning(
                "Processed the ticker data from binance. qty=%s", len(ticker_data)
            )

        logger.warning("Current tickers len=%s", len(tickers))


async def flush_tickers():
    redis_client = await connect_to_redis()

    if tickers:
        logger.warning("Flushing '%s' ticker to redis ", len(tickers))
        start = time.time()
        tickers_copy = deepcopy(tickers)
        tickers.clear()
        await flush_tickers_to_db(tickers_copy)
        for tick_name, data in tickers_copy.items():
            print(f"{data=}")
            await redis_client.hset(tick_name, key=None, value=None, mapping=data)
            # doing simple expiry per every ticker
            await redis_client.expire(tick_name, redis_expiry_time)

        end = time.time()
        logger.warning(f"It took {end - start} seconds to flush tickers to redis")

    else:
        logger.warning("No tickers to flush")

async def flush_tickers_to_db(tickers: list):
    session = await get_db_session().__anext__()
    async with session:
        for tick_name, data in tickers.items():
            ticker = BinanceTickerModel(
                ticker_name=data['ticker_name'],
                price=data['price'],
                timestamp=data['timestamp'],
            )
            session.add(ticker)

        await session.commit()


async def connect_to_binance():
    uri = binance_stream_url
    try:
        async with websockets.connect(uri) as ws:
            logger.warning("Connected to Binance websocket stream")
            await ws.send(
                json.dumps({"method": "SUBSCRIBE", "params": ["!ticker@arr"], "id": 1})
            )

            while True:
                message = await ws.recv()
                await asyncio.sleep(0)
                await process_msg(message)

    except (TimeoutError, websockets.exceptions.ConnectionClosedError) as e:
        logger.exception("Unable to connect to binance websocket: %s, Exiting app", e)
        # exiting when binance is unavailable to reflect it properly on alerts/dashboards
        sys.exit(1)

    except Exception as e:
        logger.exception(e)


def quote_consumer_main():
    loop = asyncio.get_event_loop()
    loop.create_task(connect_to_binance())
    loop.create_task(repeat(redis_flush_timeout, flush_tickers))

    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    quote_consumer_main()
