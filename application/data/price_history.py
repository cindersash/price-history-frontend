from dataclasses import dataclass
from typing import List


@dataclass
class PriceHistory:
    dates: List[str]
    prices: List[float]
    current_price: str
    minimum_price: str
    maximum_price: str
    minimum_price_date: str = None
    maximum_price_date: str = None
