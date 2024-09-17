# Crypto Converter

## Build and launch
```shell
1.docker compose build
2.docker compose up

```

## Run tests
```shell
docker compose -f docker-compose-test up
```

## Request examples:
If you state "amount_from" - you state the qty of left side  binance ticker, if you state "amount_to" - 
you will state the qty of the right side ticker currency

in binance ticker btcusdt - the leftside is 'btc', the rightside is 'usdt'

1. Get exchange rate for bitcoin in usdt usin bitcoin qty
```shell
Request:
curl --location 'http://localhost:8000/exchange/' \
--header 'Content-Type: application/json' \
--data '{
          "from": "btc",
          "to": "usdt",
          "amount_from":  "0.110002"
          
}'

Response:
{"from":"btc","to":"usdt","ticker_name":"btcusdt","ticker_price":"43006.69","amount_from":"0.110002","amount_to":"4730.82191338usdt","rate_timestamp":1706959620376}

example2:
curl --location 'http://localhost:8000/exchange/' \
--header 'Content-Type: application/json' \
--data '{
          "from": "ape",
          "to": "btc",
          "amount_from":  "0.110002"
          
}'
{"from":"ape","to":"btc","ticker_name":"apebtc","ticker_price":"0.00003201","amount_from":"0.110002","amount_to":"0.000003520064btc","rate_timestamp":1707119984391}

```

2. Get exchange rate for USDT in bitcoins by usdt qty
```shell
Request:
curl --location 'http://localhost:8000/exchange/' \
--header 'Content-Type: application/json' \
--data '{
          "from": "btc",
          "to": "usdt",
          "amount_to":  "45000"
          
}'

Response:
{"from":"btc","to":"usdt","ticker_name":"btcusdt","ticker_price":"43014.84","amount_from":"1.04615058431btc","amount_to":"45000","rate_timestamp":1706959567656}
```

## Env file  template:
```shell
TAG=crypto-converter
INSTALL_DIR=/usr/src/app
PORT_PREFIX=8
PYTHONPATH=.
PYTHONBUFFERED=1
LOG_FORMAT="%(asctime)-15s %(name)s [%(levelname)s] %(filename)s:%(lineno)d  %(message)s"
LOG_LEVEL=DEBUG
BINANCE_STREAM_NAME=!ticker@ar
BINANCE_STREAM_BASE_URL=wss://stream.binance.com:9443/stream?streams=
REDIS_HOST=redis
#REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_TICKERS_KEY=tickers
REDIS_FLUSH_TIMEOUT=30
REDIS_EXPIRY_TIME=604800
EXCHANGE_API_HOST=0.0.0.0
EXCHANGE_API_PORT=8000
QUOTE_PRICE_PRECISION=6
QUOTE_TARGET_PRECISION=12
GMT_SHIFT=3
TICKER_EXPIRATION_SEC=60
```

## watch all the tickers available
```shell
redis-cli KEYS "*"
```

## In case the ticker is older 1 min or is non-existing - you will get this error:
```shell
curl --location 'http://localhost:8000/exchange/' --header 'Content-Type: application/json' --data '{
          "from": "ape",
          "to": "btc2",
          "amount_from":  "0.110002"
          
}'
{"error":"Request failed: ('No valid ticker available for ticker %s', 'apebtc2')","status_code":503}
```

## How to add alembic to the local project
```shell
1. run
 alembic init --template async ./alembic
2. Declare sqlalchemy's declarative Base in the code
3. import Base to alembics env.py Base and add Base.metadata target_metadata
4. Run to create the very first migration 
 docker compose exec api alembic revision --autogenerate -m "your message here"
5. docker compose exec api alembic upgrade
```

## Running migrations
```shell
docker compose run api alembic revision --autogenerate -m "Your migration message"
docker compose run api alembic upgrade
```