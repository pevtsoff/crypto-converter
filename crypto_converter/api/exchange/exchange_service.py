from decimal import localcontext

from fastapi import Depends
from redis import StrictRedis

from crypto_converter.common.common import connect_to_redis
from crypto_converter.common.exceptions import NoValidTickerAvailableForTicker
from crypto_converter.common.models import (
    BinanceTicker,
    ExchangeBid,
    ExchangeResponse,
    quote_price_precision,
    target_precision,
)


class ExchangeService:
    def __init__(self, redis_client: StrictRedis = Depends(connect_to_redis)):
        self.redis_client = redis_client

    async def exchange(self, exchange_bid: ExchangeBid) -> ExchangeResponse:
        ticker = f"{exchange_bid.from_}{exchange_bid.to_}"
        ticker_obj = await self.get_ticker_from_redis(ticker)
        return await self._exchange(exchange_bid, ticker, ticker_obj)

    async def _exchange(
        self, exchange_bid: ExchangeBid, ticker: str, ticker_obj: BinanceTicker
    ) -> ExchangeResponse:
        with localcontext() as ctx:
            ctx.prec = target_precision

            if exchange_bid.amount_from:
                result = exchange_bid.amount_from * ticker_obj.get_quantized_price()
                amount_params = {
                    "amount_from": format(
                        exchange_bid.amount_from.normalize(),
                        f".{quote_price_precision}f",
                    )
                    .rstrip("0")
                    .rstrip("."),
                    "amount_to": format(result.normalize(), f".{target_precision}f")
                    .rstrip("0")
                    .rstrip(".")
                    + exchange_bid.to_,
                }

            else:
                result = exchange_bid.amount_to / ticker_obj.get_quantized_price()
                amount_params = {
                    "amount_from": format(result.normalize(), f".{target_precision}f")
                    .rstrip("0")
                    .rstrip(".")
                    + exchange_bid.from_,
                    "amount_to": format(
                        exchange_bid.amount_to.normalize(), f".{quote_price_precision}f"
                    )
                    .rstrip("0")
                    .rstrip("."),
                }

        response = ExchangeResponse(
            **{
                "from": exchange_bid.from_,
                "to": exchange_bid.to_,
                "rate_timestamp": ticker_obj.timestamp,
                "ticker_name": ticker,
                "ticker_price": ticker_obj.price.rstrip("0"),
                **amount_params,
            }
        )

        return response

    async def get_ticker_from_redis(self, ticker: str) -> BinanceTicker:
        ticker_item = await self.redis_client.hgetall(ticker)

        if ticker_item:
            ticker_obj = BinanceTicker.from_redis(ticker_item)
            ticker_obj.is_fresh()
            return ticker_obj

        else:
            raise NoValidTickerAvailableForTicker(
                "No valid ticker available for ticker %s", ticker
            )
