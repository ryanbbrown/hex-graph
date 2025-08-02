"""
Factory class for creating different hexagon archetype patterns
"""

import random
from .models import Hexagon, Territory, HexSide


class HexagonArchetypes:
    """Factory class for creating different hexagon archetype patterns"""
    
    @staticmethod
    def create_triple() -> Hexagon:
        """
        Creates a triple hexagon with three territories:
        - Territory 1: touches sides 0 and 1
        - Territory 2: touches sides 2 and 3  
        - Territory 3: touches sides 4 and 5
        All territories are connected to each other internally.
        """
        # Create three unique territories
        territory_1 = Territory(touching_sides={HexSide.SIDE_0, HexSide.SIDE_1})
        territory_2 = Territory(touching_sides={HexSide.SIDE_2, HexSide.SIDE_3})
        territory_3 = Territory(touching_sides={HexSide.SIDE_4, HexSide.SIDE_5})
        
        # Create internal edges - all territories connected to each other
        internal_edges = [
            (territory_1, territory_2),
            (territory_2, territory_3),
            (territory_1, territory_3)
        ]
        
        # Create and return the hexagon
        return Hexagon(
            territories=[territory_1, territory_2, territory_3],
            internal_edges=internal_edges
        )
    
    @staticmethod
    def create_diamond() -> Hexagon:
        """
        Creates a diamond hexagon with four territories:
        - Territory 1: touches sides 0 and 1, connects to territories 2 and 3
        - Territory 2: touches side 5, connects to territories 1, 3, and 4
        - Territory 3: touches side 2, connects to territories 1, 2, and 4  
        - Territory 4: touches sides 3 and 4, connects to territories 2 and 3
        """
        # Create four unique territories
        territory_1 = Territory(touching_sides={HexSide.SIDE_0, HexSide.SIDE_1})
        territory_2 = Territory(touching_sides={HexSide.SIDE_5})
        territory_3 = Territory(touching_sides={HexSide.SIDE_2})
        territory_4 = Territory(touching_sides={HexSide.SIDE_3, HexSide.SIDE_4})
        
        # Create internal edges - diamond pattern
        internal_edges = [
            (territory_1, territory_2),
            (territory_1, territory_3),
            (territory_2, territory_3),
            (territory_4, territory_2),
            (territory_4, territory_3)
        ]
        
        # Create and return the hexagon
        return Hexagon(
            territories=[territory_1, territory_2, territory_3, territory_4],
            internal_edges=internal_edges
        )
    
    @staticmethod
    def create_single() -> Hexagon:
        """
        Creates a single hexagon with one territory:
        - Territory 1: touches all sides (0, 1, 2, 3, 4, 5)
        No internal edges (just one territory).
        """
        # Create one territory that touches all sides
        territory_1 = Territory(touching_sides={
            HexSide.SIDE_0, HexSide.SIDE_1, HexSide.SIDE_2, 
            HexSide.SIDE_3, HexSide.SIDE_4, HexSide.SIDE_5
        })
        
        # No internal edges since there's only one territory
        internal_edges = []
        
        # Create and return the hexagon
        return Hexagon(
            territories=[territory_1],
            internal_edges=internal_edges
        )
    
    @staticmethod
    def create_five() -> Hexagon:
        """
        Creates a five hexagon with five territories:
        - Territory 1: touches side 0
        - Territory 2: touches side 1
        - Territory 3: touches side 2
        - Territory 4: touches sides 3 and 4
        - Territory 5: touches side 5
        
        Internal connections:
        T1-T2, T1-T5, T1-T3, T2-T3, T4-T3, T4-T5, T3-T5
        """
        # Create five unique territories
        territory_1 = Territory(touching_sides={HexSide.SIDE_0})
        territory_2 = Territory(touching_sides={HexSide.SIDE_1})
        territory_3 = Territory(touching_sides={HexSide.SIDE_2})
        territory_4 = Territory(touching_sides={HexSide.SIDE_3, HexSide.SIDE_4})
        territory_5 = Territory(touching_sides={HexSide.SIDE_5})
        
        # Create internal edges based on specification
        internal_edges = [
            (territory_1, territory_2),
            (territory_1, territory_5),
            (territory_1, territory_3),
            (territory_2, territory_3),
            (territory_4, territory_3),
            (territory_4, territory_5),
            (territory_3, territory_5)
        ]
        
        # Create and return the hexagon
        return Hexagon(
            territories=[territory_1, territory_2, territory_3, territory_4, territory_5],
            internal_edges=internal_edges
        )
    
    @staticmethod 
    def create_random() -> Hexagon:
        """Create a random archetype hexagon"""
        choice = random.choice(['triple', 'diamond', 'five'])
        if choice == 'triple':
            return HexagonArchetypes.create_triple()
        elif choice == 'diamond':
            return HexagonArchetypes.create_diamond()
        else:
            return HexagonArchetypes.create_five()