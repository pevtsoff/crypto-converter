import asyncio
import logging

import redis as sync_redis
import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError
from redis.exceptions import TimeoutError as redisTimeoutError

from crypto_converter.common.settings import (
    LOG_FORMAT,
    LOG_LEVEL,
    REDIS_HOST,
    REDIS_PORT,
)

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
            host=REDIS_HOST,
            port=REDIS_PORT,
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
