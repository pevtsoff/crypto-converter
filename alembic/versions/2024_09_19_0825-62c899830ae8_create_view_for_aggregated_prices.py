"""create view for aggregated prices

Revision ID: 62c899830ae8
Revises: 9b2d26cd4632
Create Date: 2024-09-19 08:25:57.783259

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "62c899830ae8"
down_revision: Union[str, None] = "9b2d26cd4632"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        """
    CREATE  VIEW aggregated_binance_prices AS
    SELECT 
        btl.id AS ticker_id,
        MIN(btad.price::FLOAT) AS min_price,
        AVG(btad.price::FLOAT) AS avg_price,
        MAX(btad.price::FLOAT) AS max_price,
        NOW() AS created_at
    FROM 
        binance_tickers_data btad
    JOIN 
        binance_tickers_list btl ON btl.id = btad.ticker_id
    WHERE 
        btad.created_at >= NOW() - INTERVAL '1 day'  -- Adjust the time frame as needed
    GROUP BY 
        btl.id;
    """
    )


def downgrade():
    op.execute(
        """
    DROP VIEW IF EXISTS aggregated_binance_prices;
    """
    )
