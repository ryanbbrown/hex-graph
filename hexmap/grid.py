"""
Grid management and hexagon connections
"""

from typing import List, Tuple, Optional
from pydantic import BaseModel
from uuid import UUID
import networkx as nx
import random

from .models import Hexagon, HexSide


class HexagonGrid(BaseModel):
    """
    Manages multiple hexagons and their connections in the overall graph
    """
    hexagons: List[Hexagon] = []
    hex_connections: List[Tuple[UUID, HexSide, UUID, HexSide]] = []  # (hex1_id, side1, hex2_id, side2)
    
    def is_side_occupied(self, hex_id: UUID, side: HexSide) -> bool:
        """Check if a specific side of a hexagon is already connected"""
        for connection in self.hex_connections:
            if (connection[0] == hex_id and connection[1] == side) or \
               (connection[2] == hex_id and connection[3] == side):
                return True
        return False
    
    def add_hexagon(self, hexagon: Hexagon, connect_to_hex_id: Optional[UUID] = None, 
                   connect_my_side: Optional[HexSide] = None, 
                   connect_their_side: Optional[HexSide] = None) -> bool:
        """
        Add a hexagon to the grid, optionally connecting it to an existing hexagon.
        Returns True if successful, False if connection failed due to occupied sides.
        """
        # Add the hexagon to the grid
        self.hexagons.append(hexagon)
        
        # If no connection specified, just add the hexagon
        if connect_to_hex_id is None:
            return True
            
        # Validate the connection
        if connect_my_side is None or connect_their_side is None:
            raise ValueError("Must specify both sides for connection")
            
        # Check if either side is already occupied
        if self.is_side_occupied(hexagon.hex_id, connect_my_side):
            print(f"Warning: Side {connect_my_side} of new hexagon {hexagon.hex_id} is already occupied")
            return False
            
        if self.is_side_occupied(connect_to_hex_id, connect_their_side):
            print(f"Warning: Side {connect_their_side} of hexagon {connect_to_hex_id} is already occupied")
            return False
        
        # Make the connection
        self.hex_connections.append((hexagon.hex_id, connect_my_side, connect_to_hex_id, connect_their_side))
        
        return True
    
    def get_hexagon_by_id(self, hex_id: UUID) -> Optional[Hexagon]:
        """Get a hexagon by its ID"""
        for hex in self.hexagons:
            if hex.hex_id == hex_id:
                return hex
        return None
    
    def extract_territory_graph(self) -> nx.Graph:
        """
        Extract the full territory graph from the hexagon grid.
        Returns a NetworkX graph with territory nodes and connections.
        """
        graph = nx.Graph()
        
        # Step 1: Add all territories as nodes and collect internal edges
        all_internal_edges = []
        for hexagon in self.hexagons:
            # Add territories as nodes
            for territory in hexagon.territories:
                graph.add_node(str(territory.territory_id), hexagon_id=str(hexagon.hex_id))
            
            # Collect internal edges
            for edge in hexagon.internal_edges:
                all_internal_edges.append((str(edge[0].territory_id), str(edge[1].territory_id)))
        
        # Step 2: Add internal edges to graph
        for edge in all_internal_edges:
            graph.add_edge(edge[0], edge[1], connection_type="internal")
        
        # Step 3: Add inter-hexagon connections based on side connections
        for connection in self.hex_connections:
            hex1_id, side1, hex2_id, side2 = connection
            
            hex1 = self.get_hexagon_by_id(hex1_id)
            hex2 = self.get_hexagon_by_id(hex2_id)
            
            if hex1 is None or hex2 is None:
                continue
                
            # Find territories that touch the connected sides
            hex1_territories = [t for t in hex1.territories if side1 in t.touching_sides]
            hex2_territories = [t for t in hex2.territories if side2 in t.touching_sides]
            
            # Smart connection logic based on territory positioning
            connections = self._get_smart_territory_connections(hex1_territories, hex2_territories, side1, side2)
            
            # Add connections to graph
            for t1, t2 in connections:
                graph.add_edge(str(t1.territory_id), str(t2.territory_id), connection_type="inter_hexagon")
        
        return graph
    
    def _get_smart_territory_connections(self, hex1_territories, hex2_territories, side1, side2):
        """
        Smart connection logic for territories on touching hexagon sides.
        Handles the case where both sides have 2 territories by using spatial positioning.
        """
        # Case 1: Either side has only 1 territory - use all-to-all (simple case)
        if len(hex1_territories) == 1 or len(hex2_territories) == 1:
            connections = []
            for t1 in hex1_territories:
                for t2 in hex2_territories:
                    connections.append((t1, t2))
            return connections
        
        # Case 2: Both sides have 2 territories - use spatial matching
        if len(hex1_territories) == 2 and len(hex2_territories) == 2:
            # Determine which territory is at "start" vs "end" of each side
            def get_territory_position(territory, side):
                prev_side = HexSide((side - 1) % 6)
                next_side = HexSide((side + 1) % 6)
                
                if prev_side in territory.touching_sides:
                    return 'start'  # Territory at counter-clockwise end
                elif next_side in territory.touching_sides:
                    return 'end'    # Territory at clockwise end
                else:
                    return 'middle' # Territory only touches this side
            
            # Categorize territories by position
            hex1_start = [t for t in hex1_territories if get_territory_position(t, side1) == 'start']
            hex1_end = [t for t in hex1_territories if get_territory_position(t, side1) == 'end']
            hex2_start = [t for t in hex2_territories if get_territory_position(t, side2) == 'start']
            hex2_end = [t for t in hex2_territories if get_territory_position(t, side2) == 'end']
            
            connections = []
            
            # Connect start of side1 to end of side2 (spatial alignment)
            for t1 in hex1_start:
                for t2 in hex2_end:
                    connections.append((t1, t2))
            
            # Connect end of side1 to start of side2 (spatial alignment)
            for t1 in hex1_end:
                for t2 in hex2_start:
                    connections.append((t1, t2))
            
            # Optional: Add one diagonal connection (as mentioned in logic.md)
            if hex1_start and hex1_end and hex2_start and hex2_end:
                if random.choice([True, False]):
                    # Connect start-to-start
                    for t1 in hex1_start:
                        for t2 in hex2_start:
                            connections.append((t1, t2))
                else:
                    # Connect end-to-end
                    for t1 in hex1_end:
                        for t2 in hex2_end:
                            connections.append((t1, t2))
            
            return connections
        
        # Fallback: use all-to-all for any other cases
        connections = []
        for t1 in hex1_territories:
            for t2 in hex2_territories:
                connections.append((t1, t2))
        return connections