from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class Trade(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    trade_id: int
    symbol: str
    price: Decimal
    quantity: Decimal
    quote_quantity: Decimal
    time: datetime
    is_buyer_maker: bool
    is_best_match: bool
    