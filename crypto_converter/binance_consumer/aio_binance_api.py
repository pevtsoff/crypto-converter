import websockets
import asyncio
import json
import sys
import time
from copy import deepcopy
from crypto_converter.common.common import configure_logger, connect_to_redis, repeat
from crypto_converter.common.models import BinanceTicker
from crypto_converter.common.settings import (
    BINANCE_STREAM_URL,
    REDIS_EXPIRY_TIME,
    REDIS_FLUSH_TIMEOUT,
)
from crypto_converter.database.db import get_db_session, transaction
from crypto_converter.database.db_models import BinanceTickerModel


logger = configure_logger(__name__)
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
                    **{"ticker_name": symbol, "price": price, "timestamp": event_time}
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
            await redis_client.hset(tick_name, key=None, value=None, mapping=data)
            # doing simple expiry per every ticker
            await redis_client.expire(tick_name, REDIS_EXPIRY_TIME)

        end = time.time()
        logger.warning(
            f"It took {end - start} seconds to flush {tickers_copy.__len__()} tickers to redis"
        )

    else:
        logger.warning("No tickers to flush")


async def flush_tickers_to_db(tickers: list):
    tickers_objects = []
    start = time.time()
    async with get_db_session() as session, transaction(session):
        for tick_name, data in tickers.items():
            if data["ticker_name"]:
                ticker = BinanceTickerModel(
                    ticker_name=data["ticker_name"],
                    price=data["price"],
                    timestamp=data["timestamp"],
                )
                session.add(ticker)
                tickers_objects.append(ticker)

    end = time.time()
    logger.info(
        f"it took {end - start} seconds to flush {tickers.__len__()} tickers to database"
    )

    # for ticker in tickers_objects:
    #     logger.warning(f"Saved ticker {ticker.id}")


async def connect_to_binance():
    uri = BINANCE_STREAM_URL
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
    loop.create_task(repeat(REDIS_FLUSH_TIMEOUT, flush_tickers))

    try:
        loop.run_forever()

    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    quote_consumer_main()
