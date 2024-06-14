import logging
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData

from clickhouse_sqlalchemy import make_session
from crypto_converter.common import configure_logger

load_dotenv()
logger = configure_logger(__name__)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
uri = f'clickhouse+native://{os.getenv("CLICKHOUSE_HOST")}:{os.getenv("CLICKHOUSE_PORT")}/default'

engine = create_engine(uri)



logger.info(f'creating base tables in clickhouse if they dont exist')



# Dependency
def get_db():
    db = make_session(engine, is_async=True)
    try:
        yield db
    finally:
        db.close()