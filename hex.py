from typing import Dict, List, Tuple, Optional, Set
from enum import IntEnum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
import random
import networkx as nx
import matplotlib.pyplot as plt
import argparse

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
    
    def extract_territory_graph(self, save_image: bool = True, use_colors: bool = False, show_ids: bool = False) -> nx.Graph:
        """
        Extract the full territory graph from the hexagon grid using Kamada-Kawai layout.
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
        
        # Step 4: Visualize with kamada-kawai layout
        if save_image:
            self._visualize_territory_graph(graph, use_colors, show_ids)
        
        return graph
    
    def _visualize_territory_graph(self, graph: nx.Graph, use_colors: bool = False, show_ids: bool = False):
        """Create a visual representation using kamada-kawai layout for even distribution"""
        plt.figure(figsize=(12, 8))
        
        # Use kamada-kawai layout for optimal distribution
        try:
            pos = nx.kamada_kawai_layout(graph)
            layout_used = "kamada_kawai"
        except Exception:
            print("Kamada-Kawai failed, falling back to spring layout...")
            pos = nx.spring_layout(graph, k=2, iterations=100)
            layout_used = "spring"
        
        # Draw nodes with different colors for different hexagons or light grey
        if use_colors:
            hexagon_colors = {}
            color_map = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']
            
            for i, hexagon in enumerate(self.hexagons):
                hexagon_colors[str(hexagon.hex_id)] = color_map[i % len(color_map)]
            
            node_colors = []
            for node in graph.nodes():
                hex_id = graph.nodes[node]['hexagon_id']
                node_colors.append(hexagon_colors[hex_id])
        else:
            node_colors = ['lightgrey'] * len(graph.nodes())
        
        # Draw internal edges (solid lines)
        internal_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('connection_type') == 'internal']
        inter_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('connection_type') == 'inter_hexagon']
        
        # Draw the graph
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=4000, alpha=0.8)
        nx.draw_networkx_edges(graph, pos, edgelist=internal_edges, edge_color='black', width=2, alpha=0.6)
        nx.draw_networkx_edges(graph, pos, edgelist=inter_edges, edge_color='red', width=3, alpha=0.8, style='dashed')
        
        # Add labels with short node IDs if requested
        if show_ids:
            labels = {node: node[:8] for node in graph.nodes()}
            nx.draw_networkx_labels(graph, pos, labels, font_size=8)
        
        plt.title(f"Territory Graph - {layout_used.title()} Layout\n(Black lines: internal connections, Red dashed: inter-hexagon connections)")
        plt.axis('off')
        plt.tight_layout()
        
        # Save the image
        plt.savefig(f'territory_graph_{layout_used}.png', dpi=300, bbox_inches='tight')
        print(f"Territory graph saved as 'territory_graph_{layout_used}.png' using {layout_used} layout")
        
        # Print some stats
        print(f"Graph has {graph.number_of_nodes()} territories and {graph.number_of_edges()} connections")
        internal_count = len(internal_edges)
        inter_count = len(inter_edges)
        print(f"Internal connections: {internal_count}")
        print(f"Inter-hexagon connections: {inter_count}")


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
    def create_random() -> Hexagon:
        """Create a random archetype hexagon"""
        choice = random.choice(['triple', 'diamond', 'five'])
        if choice == 'triple':
            return HexagonArchetypes.create_triple()
        elif choice == 'diamond':
            return HexagonArchetypes.create_diamond()
        else:
            return HexagonArchetypes.create_five()

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


def main():
    """Create a hexagon ring of 6 hexagons (like a Catan board section)"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate hexagon territory graph')
    parser.add_argument('--color', action='store_true', 
                        help='Use different colors for nodes from different hexagons (default: light grey)')
    parser.add_argument('--showids', action='store_true',
                        help='Show territory IDs on nodes (default: no IDs)')
    args = parser.parse_args()
    grid = HexagonGrid()
    
    # Create first hexagon
    hex1 = HexagonArchetypes.create_random()
    hex1.rotation = random.randint(0, 5)
    grid.add_hexagon(hex1)
    print(f"Created hex1: {'triple' if len(hex1.territories) == 3 else 'diamond'}, rotation={hex1.rotation}")
    
    # Create second hexagon - connect southwest to northeast of hex1
    hex2 = HexagonArchetypes.create_random()
    hex2.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex2,
        connect_to_hex_id=hex1.hex_id,
        connect_my_side=hex2.get_side_by_direction(HexDirection.SOUTHWEST),
        connect_their_side=hex1.get_side_by_direction(HexDirection.NORTHEAST)
    )
    print(f"Created hex2: {'triple' if len(hex2.territories) == 3 else 'diamond'}, rotation={hex2.rotation}")
    
    # Create third hexagon - connect south to north of hex2
    hex3 = HexagonArchetypes.create_random()
    hex3.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex3,
        connect_to_hex_id=hex2.hex_id,
        connect_my_side=hex3.get_side_by_direction(HexDirection.SOUTH),
        connect_their_side=hex2.get_side_by_direction(HexDirection.NORTH)
    )
    print(f"Created hex3: {'triple' if len(hex3.territories) == 3 else 'diamond'}, rotation={hex3.rotation}")
    
    # Create fourth hexagon - connect southeast to northwest of hex3
    hex4 = HexagonArchetypes.create_random()
    hex4.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex4,
        connect_to_hex_id=hex3.hex_id,
        connect_my_side=hex4.get_side_by_direction(HexDirection.SOUTHEAST),
        connect_their_side=hex3.get_side_by_direction(HexDirection.NORTHWEST)
    )
    print(f"Created hex4: {'triple' if len(hex4.territories) == 3 else 'diamond'}, rotation={hex4.rotation}")
    
    # Create fifth hexagon - connect northeast to southwest of hex4
    hex5 = HexagonArchetypes.create_random()
    hex5.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex5,
        connect_to_hex_id=hex4.hex_id,
        connect_my_side=hex5.get_side_by_direction(HexDirection.NORTHEAST),
        connect_their_side=hex4.get_side_by_direction(HexDirection.SOUTHWEST)
    )
    print(f"Created hex5: {'triple' if len(hex5.territories) == 3 else 'diamond'}, rotation={hex5.rotation}")
    
    # Create sixth hexagon - connect north to south of hex5
    hex6 = HexagonArchetypes.create_random()
    hex6.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex6,
        connect_to_hex_id=hex5.hex_id,
        connect_my_side=hex6.get_side_by_direction(HexDirection.NORTH),
        connect_their_side=hex5.get_side_by_direction(HexDirection.SOUTH)
    )
    print(f"Created hex6: {'triple' if len(hex6.territories) == 3 else 'diamond'}, rotation={hex6.rotation}")
    
    # Complete the ring - connect hex6 southeast to hex1 northwest
    final_connection = (
        hex6.hex_id, 
        hex6.get_side_by_direction(HexDirection.SOUTHEAST),
        hex1.hex_id,
        hex1.get_side_by_direction(HexDirection.NORTHWEST)
    )
    grid.hex_connections.append(final_connection)
    print("Completed the hexagon ring!")
    
    # Create center hexagon with single territory
    center_hex = HexagonArchetypes.create_single()
    center_hex.rotation = random.randint(0, 5)
    grid.add_hexagon(center_hex)
    print(f"Created center hex: single territory, rotation={center_hex.rotation}")
    
    # Connect center hexagon to all 6 ring hexagons
    ring_hexagons = [hex1, hex2, hex3, hex4, hex5, hex6]
    
    for i, ring_hex in enumerate(ring_hexagons):
        # Center hexagon side i connects to ring hexagon's inner-facing side
        center_side = HexSide(i)  # Side 0, 1, 2, 3, 4, 5
        ring_inner_side = HexSide((i + 3) % 6)  # Opposite side faces center
        
        # Make the connection
        grid.hex_connections.append((
            center_hex.hex_id,
            center_side,
            ring_hex.hex_id,
            ring_inner_side
        ))
        print(f"Connected center side {center_side} to hex{i+1} side {ring_inner_side}")
    
    print("Connected center hexagon to all ring hexagons!")
    
    # Print summary
    print(f"\nCreated hexagon grid with {len(grid.hexagons)} hexagons and {len(grid.hex_connections)} connections")
    for i, connection in enumerate(grid.hex_connections):
        print(f"Connection {i+1}: {str(connection[0])[:8]}... side {connection[1]} ↔ {str(connection[2])[:8]}... side {connection[3]}")
    
    # Extract and visualize the territory graph
    print("\nExtracting territory graph...")
    territory_graph = grid.extract_territory_graph(save_image=True, use_colors=args.color, show_ids=args.showids)
    
    return grid


if __name__ == "__main__":
    main()