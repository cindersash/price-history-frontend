from dataclasses import dataclass
from typing import List


@dataclass
class PriceHistory:
    dates: List[str]
    prices: List[int]
    minimum_price: str
    maximum_price: str
