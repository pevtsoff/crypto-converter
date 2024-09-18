from datetime import datetime
from typing import List
from sqlalchemy import BigInteger, String, JSON, ForeignKey, Float, DDL
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
import sqlalchemy as sa


Base = declarative_base()


class BinanceTickerDataModel(Base):
    __tablename__ = "binance_tickers_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("binance_tickers_list.id", ondelete="CASCADE")
    )
    ticker: Mapped["BinanceTickersModel"] = relationship()

    price: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[BigInteger] = mapped_column(BigInteger)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=True)

    json_data = mapped_column(JSON)


class BinanceTickerAggregatedData(Base):
    __tablename__ = "binance_tickers_aggregated_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("binance_tickers_list.id", ondelete="CASCADE")
    )
    ticker: Mapped["BinanceTickersModel"] = relationship()

    min_price: Mapped[float] = mapped_column(Float(50))
    avg_price: Mapped[float] = mapped_column(Float(50))
    max_price: Mapped[float] = mapped_column(Float(50))

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=True)


class BinanceTickersModel(Base):
    __tablename__ = "binance_tickers_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_name: Mapped[str] = mapped_column(String(50), index=True)
    ticker_data: Mapped[List[BinanceTickerDataModel]] = relationship(
        # cascade="all, delete-orphan",
        passive_deletes="all"
    )
    ticker_aggregated_data: Mapped[List[BinanceTickerAggregatedData]] = relationship(
        passive_deletes="all"
    )


function_ddl = DDL(
    """
CREATE OR REPLACE FUNCTION update_aggregates()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO binance_ticker_aggregates (ticker_id, min_price, max_price, avg_price)
    VALUES (NEW.ticker_id, NEW.price, NEW.price, NEW.price)
    ON CONFLICT (ticker_id)
    DO UPDATE SET
        min_price = LEAST(binance_ticker_aggregates.min_price, NEW.price),
        max_price = GREATEST(binance_ticker_aggregates.max_price, NEW.price),
        avg_price = (binance_ticker_aggregates.avg_price + NEW.price) / 2;  -- Adjust as needed
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

trigger_ddl = DDL(
    """
CREATE TRIGGER update_aggregates_trigger
AFTER INSERT ON binance_tickers_data
FOR EACH ROW EXECUTE FUNCTION update_aggregates();
"""
)
