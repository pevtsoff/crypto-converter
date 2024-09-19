"""new migration

Revision ID: 9b2d26cd4632
Revises: 642ab3980717
Create Date: 2024-09-18 13:38:44.414004

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import DDL

# revision identifiers, used by Alembic.
revision: str = "9b2d26cd4632"
down_revision: Union[str, None] = "642ab3980717"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Function to update aggregated price data
aggregation_function_ddl = DDL(
    """
CREATE OR REPLACE FUNCTION update_aggregated_prices() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO binance_tickers_aggregated_data (ticker_id, min_price, avg_price, max_price, created_at)
    SELECT 
        NEW.ticker_id,
        MIN(price::FLOAT),
        AVG(price::FLOAT),
        MAX(price::FLOAT),
        NOW()
    FROM binance_tickers_data
    WHERE ticker_id = NEW.ticker_id
    ON CONFLICT (ticker_id)
    DO UPDATE SET
        min_price = EXCLUDED.min_price,
        avg_price = EXCLUDED.avg_price,
        max_price = EXCLUDED.max_price,
        created_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)

# Trigger to call the update_aggregated_prices function
aggregation_trigger_ddl = DDL(
    """
CREATE TRIGGER binance_data_aggregation_trigger
AFTER INSERT OR UPDATE ON binance_tickers_data
FOR EACH ROW EXECUTE FUNCTION update_aggregated_prices();
"""
)


def upgrade() -> None:
    # Create the aggregation function and trigger
    op.execute(aggregation_function_ddl)
    op.execute(aggregation_trigger_ddl)
    op.create_unique_constraint(None, "binance_tickers_aggregated_data", ["ticker_id"])


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS binance_data_aggregation_trigger ON binance_tickers_data;"
    )
    # Drop the function
    op.execute("DROP FUNCTION IF EXISTS update_aggregated_prices;")
    # Drop the aggregated data table
    op.drop_constraint(None, "binance_tickers_aggregated_data", type_="unique")
