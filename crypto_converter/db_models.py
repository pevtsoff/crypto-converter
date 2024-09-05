from pip._vendor.rich.table import Column
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, BigInteger

Base = declarative_base()


class BinanceTickerModel(Base):
    __tablename__ = "binance_tickers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker_name: Mapped[str] = mapped_column(String(50))
    price: Mapped[str] = mapped_column(String(50))
    timestamp: Mapped[BigInteger] = mapped_column(BigInteger)
