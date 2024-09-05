import os

from dotenv import load_dotenv

load_dotenv()

LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)-15s %(name)s [%(levelname)s] %(filename)s:%(lineno)d  %(message)s",
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TICKER_KEY = os.getenv("REDIS_TICKERS_KEY", "tickers")

PG_URL = os.getenv("PG_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
SQL_DEBUG = bool(os.getenv("SQL_DEBUG", False))

REDIS_FLUSH_TIMEOUT = int(os.getenv("REDIS_FLUSH_TIMEOUT", 30))
REDIS_EXPIRY_TIME = int(os.getenv("REDIS_EXPIRY_TIME", 3600))

BINANCE_STREAM_NAME = os.getenv("BINANCE_STREAM_NAME", "")
BINANCE_STREAM_BASE_URL = os.getenv(
    "BINANCE_STREAM_BASE_URL", "wss://stream.binance.com:9443/stream?streams="
)
BINANCE_STREAM_URL = BINANCE_STREAM_BASE_URL + BINANCE_STREAM_NAME

exchange_api_host = os.getenv("EXCHANGE_API_HOST", "0.0.0.0")
exchange_api_port = os.getenv("EXCHANGE_API_PORT", 8000)
