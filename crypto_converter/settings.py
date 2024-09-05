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
