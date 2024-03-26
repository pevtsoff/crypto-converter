import asyncio
import logging
import os
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import (
    BusyLoadingError,
    ConnectionError,
    TimeoutError as redisTimeoutError,
)
import redis.asyncio as redis
import redis as sync_redis


LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)-15s %(name)s [%(levelname)s] %(filename)s:%(lineno)d  %(message)s",
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")


redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_tickers_key = os.getenv("REDIS_TICKERS_KEY", "tickers")
retry = Retry(ExponentialBackoff(), 3)


def configure_logger(name: str, log_level: str = LOG_LEVEL):
    logging.basicConfig(format=LOG_FORMAT)
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    return logger


logger = configure_logger(__name__)


async def repeat(interval, func, *args, **kwargs):
    while True:
        func_name = func.__name__
        logger.warning(f"running periodic task '{func_name}'")

        try:
            await func(*args, **kwargs)

        except Exception as e:
            logger.exception(f"Error running {func_name}: {e}")

        await asyncio.sleep(interval)


async def connect_to_redis():
    try:
        redis_client = await redis.StrictRedis(
            host=redis_host,
            port=redis_port,
            retry=retry,
            retry_on_error=[BusyLoadingError, ConnectionError, redisTimeoutError],
        )

        await redis_client.ping()

    except sync_redis.exceptions.ConnectionError:
        logger.exception(
            "Cant connect to redis at this moment, "
            "will be retrying on the next flush attempt"
        )
        raise

    return redis_client
