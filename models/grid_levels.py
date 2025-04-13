from dataclasses import dataclass
from typing import List

#TODO: remove dataclass
@dataclass
class GridLevels:
    levels: List[float]
    min: float
    max: float