from dataclasses import dataclass
from typing import List

@dataclass
class GridLevels:
    levels: List[float]
    min: float
    max: float