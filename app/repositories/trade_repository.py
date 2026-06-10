from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trade import Trade


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def get_by_symbol(self, symbol: str, limit: int) -> list[Trade]:
        result = await self._session.execute(
            select(Trade)
            .where(Trade.symbol == symbol)
            .order_by(Trade.time.desc())
            .limit(limit)
        )

        return list(result.scalars().all())
    
    async def bulk_insert(self, trades: list[dict]) -> int: # pyright: ignore[reportReturnType]
        """Persists a list of normalized trades to the database.

        Inserts new records and skips existing ones based on trade_id conflict.

        Args:
            trades: List of dicts with keys matching the Trade model columns.

        Returns:
            Number of records sent to the database (inserted + skipped).
        """
        try:
            stmt = ( 
                insert(Trade)
                .values(trades)
                .on_conflict_do_nothing( 
                    index_elements=["trade_id"],
                )
            )

            await self._session.execute(stmt)
            await self._session.commit()
            
            return len(trades)
        except SQLAlchemyError:
            await self._session.rollback()
            raise