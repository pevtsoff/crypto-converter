import datetime
import os
import time
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from crypto_converter.common.common import configure_logger
from crypto_converter.common.exceptions import NoValidTickerAvailableForTicker

quote_price_precision = int(os.getenv("QUOTE_PRICE_PRECISION", 6))
target_precision = int(os.getenv("QUOTE_TARGET_PRECISION", 12))
ticker_expiration = int(os.getenv("TICKER_EXPIRATION_SEC", 60))
logger = configure_logger(__name__)


def quantize(value: Decimal, precision: int = quote_price_precision) -> Decimal:
    # Using precision 20 for proper rounding to 6 precision decimal
    with localcontext() as ctx:
        ctx.prec = target_precision * 2
        d = (
            Decimal(value)
            .quantize(Decimal("10") ** -precision, rounding=ROUND_HALF_EVEN)
            .normalize()
        )

    return d


class ExchangeBid(BaseModel):
    from_: str = Field(alias="from")
    to_: str = Field(alias="to")
    amount_from: Optional[
        Annotated[
            Decimal, Field(strict=True, gt=0, decimal_places=quote_price_precision)
        ]
    ] = None
    amount_to: Optional[
        Annotated[
            Decimal, Field(strict=True, gt=0, decimal_places=quote_price_precision)
        ]
    ] = None

    @field_validator("amount_to", "amount_from", mode="before")
    @classmethod
    def wrap_to_decimal(cls, value):
        return Decimal(str(value))

    @model_validator(mode="before")
    @classmethod
    def check_amounts(cls, data: dict) -> dict:
        if isinstance(data, str) or isinstance(data, bytes):
            raise ValueError("You should send a valid json in the body")

        if all([data.get("amount_from"), data.get("amount_to")]):
            raise ValueError("amount_from and amount_to cannot be set together")
        elif not any([data.get("amount_from"), data.get("amount_to")]):
            raise ValueError("amount_from or amount_to should be passed")
        else:
            return data


class ExchangeResponse(BaseModel):
    from_: str = Field(alias="from")
    to_: str = Field(alias="to")
    ticker_name: str
    ticker_price: str
    amount_from: str
    amount_to: str
    rate_timestamp: int

    class Config:
        populate_by_name = True


class BinanceTicker(BaseModel):
    ticker_name: str
    price: str
    timestamp: int

    def is_fresh(self):
        binance_timestamp = datetime.datetime.fromtimestamp(
            int(self.timestamp / 1000), datetime.UTC
        )
        current_utc_time = datetime.datetime.fromtimestamp(time.time(), datetime.UTC)
        time_delta = current_utc_time - binance_timestamp

        if time_delta.seconds >= ticker_expiration:
            logger.warning("Ticker is too old %s", self)
            raise NoValidTickerAvailableForTicker(
                f"The ticker {self} is too old for exchange"
            )

        else:
            return True

    @staticmethod
    def from_redis(redis_obj: dict[bytes, Any]):
        data = {
            key.decode("utf-8"): value.decode("utf-8")
            for key, value in redis_obj.items()
        }
        return BinanceTicker(**data)

    def get_quantized_price(self):
        return quantize(self.price)


class BinanceTickerAggregationInfoResponse(BaseModel):
    ticker_name: str
    min_price: float
    max_price: float
    avg_price: float
    timestamp: datetime

    class Config:
        arbitrary_types_allowed = True
