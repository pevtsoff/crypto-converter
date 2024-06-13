import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, MetaData

from clickhouse_sqlalchemy import (
    Table, make_session, get_declarative_base, types, engines
)

from crypto_converter.common import configure_logger

load_dotenv()
logger = configure_logger(__name__)
uri = f'clickhouse+native://{os.getenv("CLICKHOUSE_HOST")}:{os.getenv("CLICKHOUSE_PORT")}/default'

engine = create_engine(uri)
SessionLocal = make_session(engine)
#metadata = MetaData(bind=engine)
metadata = MetaData()


logger.info(f'creating base tables in clickhouse if they dont exist')
Base = get_declarative_base(metadata=metadata)
Base.metadata.create_all(engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()