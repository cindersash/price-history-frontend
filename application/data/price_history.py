from dataclasses import dataclass
from typing import List


@dataclass
class PriceHistory:
    dates: List[str]
    prices: List[int]
    current_price: str
    minimum_price: str
    maximum_price: str
