"""
Command line interface for hexmap territory generation
"""

import argparse
import random
from typing import List, Optional

from .models import HexDirection
from .archetypes import HexagonArchetypes
from .grid import HexagonGrid
from .visualization import TerritoryVisualizer


def create_supply_territories(grid: HexagonGrid, supply_mode: str) -> Optional[List[str]]:
    """
    Create supply territories based on the specified mode.
    
    Args:
        grid: The hexagon grid containing all territories
        supply_mode: 'none', 'distributed', or 'random'
    
    Returns:
        List of territory IDs to outline, or None if mode is 'none'
    """
    if supply_mode == 'none':
        return None
    
    # Get all territory IDs from the grid
    all_territories = []
    for hexagon in grid.hexagons:
        for territory in hexagon.territories:
            all_territories.append(str(territory.territory_id))
    
    if supply_mode == 'distributed':
        # Select one territory from each hexagon
        supply_territories = []
        for hexagon in grid.hexagons:
            if hexagon.territories:
                selected_territory = random.choice(hexagon.territories)
                supply_territories.append(str(selected_territory.territory_id))
        return supply_territories
    
    elif supply_mode == 'random':
        # Select 7 random territories from all territories
        return random.sample(all_territories, min(7, len(all_territories)))
    
    return None


def create_hexagon_ring(center_type: str) -> HexagonGrid:
    """Create a hexagon ring of 6 hexagons (like a Catan board section) with center hex"""
    grid = HexagonGrid()
    
    # Create first hexagon
    hex1 = HexagonArchetypes.create_random()
    hex1.rotation = random.randint(0, 5)
    grid.add_hexagon(hex1)
    print(f"Created hex1: {'triple' if len(hex1.territories) == 3 else 'diamond' if len(hex1.territories) == 4 else 'five'}, rotation={hex1.rotation}")
    
    # Create second hexagon - connect southwest to northeast of hex1
    hex2 = HexagonArchetypes.create_random()
    hex2.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex2,
        connect_to_hex_id=hex1.hex_id,
        connect_my_side=hex2.get_side_by_direction(HexDirection.SOUTHWEST),
        connect_their_side=hex1.get_side_by_direction(HexDirection.NORTHEAST)
    )
    print(f"Created hex2: {'triple' if len(hex2.territories) == 3 else 'diamond' if len(hex2.territories) == 4 else 'five'}, rotation={hex2.rotation}")
    
    # Create third hexagon - connect south to north of hex2
    hex3 = HexagonArchetypes.create_random()
    hex3.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex3,
        connect_to_hex_id=hex2.hex_id,
        connect_my_side=hex3.get_side_by_direction(HexDirection.SOUTH),
        connect_their_side=hex2.get_side_by_direction(HexDirection.NORTH)
    )
    print(f"Created hex3: {'triple' if len(hex3.territories) == 3 else 'diamond' if len(hex3.territories) == 4 else 'five'}, rotation={hex3.rotation}")
    
    # Create fourth hexagon - connect southeast to northwest of hex3
    hex4 = HexagonArchetypes.create_random()
    hex4.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex4,
        connect_to_hex_id=hex3.hex_id,
        connect_my_side=hex4.get_side_by_direction(HexDirection.SOUTHEAST),
        connect_their_side=hex3.get_side_by_direction(HexDirection.NORTHWEST)
    )
    print(f"Created hex4: {'triple' if len(hex4.territories) == 3 else 'diamond' if len(hex4.territories) == 4 else 'five'}, rotation={hex4.rotation}")
    
    # Create fifth hexagon - connect northeast to southwest of hex4
    hex5 = HexagonArchetypes.create_random()
    hex5.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex5,
        connect_to_hex_id=hex4.hex_id,
        connect_my_side=hex5.get_side_by_direction(HexDirection.NORTHEAST),
        connect_their_side=hex4.get_side_by_direction(HexDirection.SOUTHWEST)
    )
    print(f"Created hex5: {'triple' if len(hex5.territories) == 3 else 'diamond' if len(hex5.territories) == 4 else 'five'}, rotation={hex5.rotation}")
    
    # Create sixth hexagon - connect north to south of hex5
    hex6 = HexagonArchetypes.create_random()
    hex6.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex6,
        connect_to_hex_id=hex5.hex_id,
        connect_my_side=hex6.get_side_by_direction(HexDirection.NORTH),
        connect_their_side=hex5.get_side_by_direction(HexDirection.SOUTH)
    )
    print(f"Created hex6: {'triple' if len(hex6.territories) == 3 else 'diamond' if len(hex6.territories) == 4 else 'five'}, rotation={hex6.rotation}")
    
    # Complete the ring - connect hex6 southeast to hex1 northwest
    final_connection = (
        hex6.hex_id, 
        hex6.get_side_by_direction(HexDirection.SOUTHEAST),
        hex1.hex_id,
        hex1.get_side_by_direction(HexDirection.NORTHWEST)
    )
    grid.hex_connections.append(final_connection)
    print("Completed the hexagon ring!")
    
    # Create center hexagon based on user choice
    if center_type == 'single':
        center_hex = HexagonArchetypes.create_single()
        center_type_desc = 'single'
    elif center_type == 'diamond':
        center_hex = HexagonArchetypes.create_diamond()
        center_type_desc = 'diamond'
    elif center_type == 'triple':
        center_hex = HexagonArchetypes.create_triple()
        center_type_desc = 'triple'
    elif center_type == 'five':
        center_hex = HexagonArchetypes.create_five()
        center_type_desc = 'five'
    else:  # random
        center_hex = HexagonArchetypes.create_random()
        center_type_desc = 'random'
    
    center_hex.rotation = random.randint(0, 5)
    grid.add_hexagon(center_hex)
    print(f"Created center hex: {center_type_desc} territory, rotation={center_hex.rotation}")
    
    # Connect center hexagon to all 6 ring hexagons
    ring_hexagons = [hex1, hex2, hex3, hex4, hex5, hex6]
    
    for i, ring_hex in enumerate(ring_hexagons):
        # Center hexagon side i connects to ring hexagon's inner-facing side
        from .models import HexSide
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
    
    return grid


def main():
    """Main entry point for the hexmap CLI"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate hexagon territory graph')
    parser.add_argument('--color', action='store_true', 
                        help='Use different colors for nodes from different hexagons (default: light grey)')
    parser.add_argument('--showids', action='store_true',
                        help='Show territory IDs on nodes (default: no IDs)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output filename for the graph image, saved to outputs/ folder (default: outputs/territory_graph_<layout>.png)')
    parser.add_argument('--center', '-c', type=str, choices=['single', 'diamond', 'triple', 'five', 'random'], 
                        default='random', help='Center hexagon archetype (default: random)')
    parser.add_argument('--supply', '-s', type=str, choices=['none', 'distributed', 'random'], 
                        default='none', help='Supply territories to outline: none, distributed (one per hex), or random (default: none)')
    args = parser.parse_args()
    
    # Create the hexagon grid
    grid = create_hexagon_ring(args.center)
    
    # Create supply territories
    supply_territories = create_supply_territories(grid, args.supply)
    
    # Process output filename to ensure it goes to outputs folder
    import os
    if args.output is not None:
        # If user specified a filename, put it in outputs/
        output_filename = os.path.join("outputs", args.output)
    else:
        # Default filename will be handled by visualizer
        output_filename = None
    
    # Create visualizer and generate the output
    print("\nExtracting territory graph...")
    visualizer = TerritoryVisualizer(grid)
    territory_graph = visualizer.create_and_save_visualization(
        use_colors=args.color,
        show_ids=args.showids,
        output_filename=output_filename,
        supply_territories=supply_territories
    )
    
    return grid


if __name__ == "__main__":
    main()