"""
Grid management and hexagon connections
"""

from typing import List, Tuple, Optional
from pydantic import BaseModel
from uuid import UUID
import networkx as nx

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
            
            # Connect all territories from side1 to all territories from side2
            for t1 in hex1_territories:
                for t2 in hex2_territories:
                    graph.add_edge(str(t1.territory_id), str(t2.territory_id), connection_type="inter_hexagon")
        
        return graph