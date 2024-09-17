from datetime import datetime
from typing import List
from sqlalchemy import BigInteger, String, JSON, ForeignKey
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
import sqlalchemy as sa


Base = declarative_base()


class BinanceTickerModel(Base):
    __tablename__ = "binance_tickers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_name: Mapped[str] = mapped_column(String(50))
    price: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[BigInteger] = mapped_column(BigInteger)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=True)


class BinanceTickerDataModel(Base):
    __tablename__ = "binance_tickers_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    ticker_id: Mapped[int] = mapped_column(ForeignKey("binance_tickers_list.id"))
    ticker: Mapped["BinanceTickersModel"] = relationship(back_populates="ticker_data")

    price: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[BigInteger] = mapped_column(BigInteger)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=True)

    json_data = mapped_column(JSON)


class BinanceTickersModel(Base):
    __tablename__ = "binance_tickers_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_name: Mapped[str] = mapped_column(String(50))
    ticker_data: Mapped[List[BinanceTickerDataModel]] = relationship()
