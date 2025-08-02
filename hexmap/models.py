"""
Core data models for hexagon territories and grid structures
"""

from typing import List, Tuple, Set
from enum import IntEnum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class HexSide(IntEnum):
    """Enumeration for hexagon sides, numbered 0-5"""
    SIDE_0 = 0
    SIDE_1 = 1
    SIDE_2 = 2
    SIDE_3 = 3
    SIDE_4 = 4
    SIDE_5 = 5


class HexDirection(IntEnum):
    NORTH = 0
    NORTHEAST = 1  
    SOUTHEAST = 2
    SOUTH = 3
    SOUTHWEST = 4
    NORTHWEST = 5


class Territory(BaseModel):
    """Represents a territory within a hexagon"""
    territory_id: UUID = Field(default_factory=uuid4)
    touching_sides: Set[HexSide]


class Hexagon(BaseModel):
    """
    Represents a hexagon divided into territories that can be rotated and connected
    """
    hex_id: UUID = Field(default_factory=uuid4)
    territories: List[Territory]
    internal_edges: List[Tuple[Territory, Territory]]
    rotation: int = 0  # Current rotation (0-5), where 0 means side 0 is "top"

    def get_side_by_direction(self, direction: HexDirection) -> HexSide:
        """Get the actual side number for a conceptual direction based on current rotation"""
        return HexSide((direction.value + self.rotation) % 6)