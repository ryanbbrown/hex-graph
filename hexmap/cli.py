"""
Command line interface for hexmap territory generation
"""

import argparse
import random
import os
from typing import List, Optional
import networkx as nx

from .models import HexDirection
from .archetypes import HexagonArchetypes
from .grid import HexagonGrid
from .visualization import TerritoryVisualizer


def create_supply_territories(grid: HexagonGrid, supply_mode: str, num_supply: int = 5) -> Optional[List[str]]:
    """
    Create supply territories based on the specified mode.
    
    Args:
        grid: The hexagon grid containing all territories
        supply_mode: 'none', 'random', 'oneperhex', or 'algo'
        num_supply: Number of supply centers to select
    
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
    
    if supply_mode == 'oneperhex':
        if num_supply != 7:
            raise ValueError(f"oneperhex mode requires exactly 7 supply centers (one per hexagon), but {num_supply} was requested")
        
        # Select one territory from each hexagon
        supply_territories = []
        for hexagon in grid.hexagons:
            if hexagon.territories:
                selected_territory = random.choice(hexagon.territories)
                supply_territories.append(str(selected_territory.territory_id))
        return supply_territories
    
    elif supply_mode == 'random':
        # Select random territories from all territories
        return random.sample(all_territories, min(num_supply, len(all_territories)))
    
    elif supply_mode == 'algo':
        # Algorithm to ensure supply centers are at least 2 edges apart
        return _create_supply_territories_algo(grid, num_supply)
    
    return None


def _create_supply_territories_algo(grid: HexagonGrid, num_supply: int, max_retries: int = 5) -> List[str]:
    """
    Create supply territories using the algorithm that ensures minimum 2-edge distance.
    
    Args:
        grid: The hexagon grid containing all territories
        num_supply: Number of supply centers to select
        max_retries: Maximum number of retry attempts
    
    Returns:
        List of territory IDs for supply centers
    """
    
    # Get the territory graph
    territory_graph = grid.extract_territory_graph()
    all_territory_ids = list(territory_graph.nodes())
    
    if num_supply > len(all_territory_ids):
        raise ValueError(f"Cannot select {num_supply} supply centers from only {len(all_territory_ids)} territories")
    
    for attempt in range(max_retries):
        try:
            # Create a copy of available territories for this attempt
            available_territories = set(all_territory_ids)
            selected_supply_centers = []
            
            while len(selected_supply_centers) < num_supply and available_territories:
                # Select a random territory from available ones
                selected_territory = random.choice(list(available_territories))
                selected_supply_centers.append(selected_territory)
                
                # Remove the selected territory and all territories within 2 edges
                territories_to_remove = set([selected_territory])
                
                # Find all territories within 2 edges using BFS
                for distance in range(1, 3):  # distance 1 and 2
                    new_territories_to_remove = set()
                    for territory in territories_to_remove:
                        if territory in territory_graph:
                            neighbors = set(territory_graph.neighbors(territory))
                            new_territories_to_remove.update(neighbors)
                    territories_to_remove.update(new_territories_to_remove)
                
                # Remove all these territories from available set
                available_territories -= territories_to_remove
            
            # Check if we got enough supply centers
            if len(selected_supply_centers) == num_supply:
                return selected_supply_centers
            
        except Exception as e:
            # If this attempt failed, continue to next attempt
            continue
    
    # If all attempts failed, raise an error
    raise RuntimeError(f"Failed to select {num_supply} supply centers with minimum 2-edge distance after {max_retries} attempts. "
                      f"This may indicate the graph is too small or dense for the requested number of supply centers.")


def create_random_archetype(archetype_filter: str) -> object:
    """
    Create a random archetype based on the specified filter.
    
    Args:
        archetype_filter: 'standard_only', 'expanded_only', or 'all'
    
    Returns:
        A randomly selected hexagon archetype
    """
    if archetype_filter == 'standard_only':
        choices = ['triple_standard', 'diamond_standard', 'five_standard']
    elif archetype_filter == 'expanded_only':
        choices = ['triple_expanded', 'diamond_expanded', 'diamond_maximal']
    else:  # 'all'
        choices = ['triple_standard', 'diamond_standard', 'five_standard', 
                  'triple_expanded', 'diamond_expanded', 'diamond_maximal']
    
    choice = random.choice(choices)
    
    if choice == 'triple_standard':
        return HexagonArchetypes.create_triple_standard()
    elif choice == 'diamond_standard':
        return HexagonArchetypes.create_diamond_standard()
    elif choice == 'five_standard':
        return HexagonArchetypes.create_five_standard()
    elif choice == 'triple_expanded':
        return HexagonArchetypes.create_triple_expanded()
    elif choice == 'diamond_expanded':
        return HexagonArchetypes.create_diamond_expanded()
    elif choice == 'diamond_maximal':
        return HexagonArchetypes.create_diamond_maximal()


def create_hexagon_ring(center_type: str, archetype_filter: str = 'all') -> HexagonGrid:
    """
    Create a hexagon ring of 6 hexagons (like a Catan board section) with center hex
    
    Args:
        center_type: Type of center hexagon ('single', 'diamond', 'triple', 'five', 'random')
        archetype_filter: Filter for ring hexagon archetypes ('standard_only', 'expanded_only', 'all')
    """
    grid = HexagonGrid()
    
    # Create first hexagon, which will be the bottom of the ring
    hex1 = create_random_archetype(archetype_filter)
    hex1.rotation = random.randint(0, 5)
    grid.add_hexagon(hex1)
    print(f"Created hex1: {'triple' if len(hex1.territories) == 3 else 'diamond' if len(hex1.territories) == 4 else 'five'}, rotation={hex1.rotation}")
    
    # Create second hexagon - connect southwest to northeast of hex1
    hex2 = create_random_archetype(archetype_filter)
    hex2.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex2,
        connect_to_hex_id=hex1.hex_id,
        connect_my_side=hex2.get_side_by_direction(HexDirection.SOUTHWEST),
        connect_their_side=hex1.get_side_by_direction(HexDirection.NORTHEAST)
    )
    print(f"Created hex2: {'triple' if len(hex2.territories) == 3 else 'diamond' if len(hex2.territories) == 4 else 'five'}, rotation={hex2.rotation}")
    
    # Create third hexagon - connect south to north of hex2
    hex3 = create_random_archetype(archetype_filter)
    hex3.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex3,
        connect_to_hex_id=hex2.hex_id,
        connect_my_side=hex3.get_side_by_direction(HexDirection.SOUTH),
        connect_their_side=hex2.get_side_by_direction(HexDirection.NORTH)
    )
    print(f"Created hex3: {'triple' if len(hex3.territories) == 3 else 'diamond' if len(hex3.territories) == 4 else 'five'}, rotation={hex3.rotation}")
    
    # Create fourth hexagon - connect southeast to northwest of hex3
    hex4 = create_random_archetype(archetype_filter)
    hex4.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex4,
        connect_to_hex_id=hex3.hex_id,
        connect_my_side=hex4.get_side_by_direction(HexDirection.SOUTHEAST),
        connect_their_side=hex3.get_side_by_direction(HexDirection.NORTHWEST)
    )
    print(f"Created hex4: {'triple' if len(hex4.territories) == 3 else 'diamond' if len(hex4.territories) == 4 else 'five'}, rotation={hex4.rotation}")
    
    # Create fifth hexagon - connect northeast to southwest of hex4
    hex5 = create_random_archetype(archetype_filter)
    hex5.rotation = random.randint(0, 5)
    grid.add_hexagon(
        hex5,
        connect_to_hex_id=hex4.hex_id,
        connect_my_side=hex5.get_side_by_direction(HexDirection.NORTHEAST),
        connect_their_side=hex4.get_side_by_direction(HexDirection.SOUTHWEST)
    )
    print(f"Created hex5: {'triple' if len(hex5.territories) == 3 else 'diamond' if len(hex5.territories) == 4 else 'five'}, rotation={hex5.rotation}")
    
    # Create sixth hexagon - connect north to south of hex5
    hex6 = create_random_archetype(archetype_filter)
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
    elif center_type == 'triple_standard':
        center_hex = HexagonArchetypes.create_triple_standard()
        center_type_desc = 'triple_standard'
    elif center_type == 'triple_expanded':
        center_hex = HexagonArchetypes.create_triple_expanded()
        center_type_desc = 'triple_expanded'
    elif center_type == 'diamond_standard':
        center_hex = HexagonArchetypes.create_diamond_standard()
        center_type_desc = 'diamond_standard'
    elif center_type == 'diamond_expanded':
        center_hex = HexagonArchetypes.create_diamond_expanded()
        center_type_desc = 'diamond_expanded'
    elif center_type == 'diamond_maximal':
        center_hex = HexagonArchetypes.create_diamond_maximal()
        center_type_desc = 'diamond_maximal'
    elif center_type == 'five_standard':
        center_hex = HexagonArchetypes.create_five_standard()
        center_type_desc = 'five_standard'
    else:  # random
        center_hex = HexagonArchetypes.create_random()
        center_type_desc = 'random'
    
    center_hex.rotation = random.randint(0, 5)
    grid.add_hexagon(center_hex)
    print(f"Created center hex: {center_type_desc} territory, rotation={center_hex.rotation}")
    
    # Connect center hexagon to all 6 ring hexagons
    ring_hexagons = [hex1, hex2, hex3, hex4, hex5, hex6]
    
    # Explicit mapping of ring hexagon connections to center
    ring_to_center_mapping = [
        (HexDirection.NORTH, HexDirection.SOUTH),         # Hex1 North → center South
        (HexDirection.NORTHWEST, HexDirection.SOUTHEAST), # Hex2 Northwest → center Southeast  
        (HexDirection.SOUTHWEST, HexDirection.NORTHEAST), # Hex3 Southwest → center Northeast
        (HexDirection.SOUTH, HexDirection.NORTH),         # Hex4 South → center North
        (HexDirection.SOUTHEAST, HexDirection.NORTHWEST), # Hex5 Southeast → center Northwest
        (HexDirection.NORTHEAST, HexDirection.SOUTHWEST)  # Hex6 Northeast → center Southwest
    ]
    
    for i, ring_hex in enumerate(ring_hexagons):
        ring_direction, center_direction = ring_to_center_mapping[i]
        
        # Convert directions to actual sides based on each hexagon's rotation
        center_side = center_hex.get_side_by_direction(center_direction)
        ring_side = ring_hex.get_side_by_direction(ring_direction)
        
        # Make the connection
        grid.hex_connections.append((
            center_hex.hex_id,
            center_side,
            ring_hex.hex_id,
            ring_side
        ))
        print(f"Connected center {center_direction} (side {center_side}) to hex{i+1} {ring_direction} (side {ring_side})")
    
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
    parser.add_argument('--showsides', action='store_true',
                        help='Show which hexagon sides each territory is touching (default: no sides)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output filename for the graph image, saved to outputs/ folder (default: outputs/territory_graph_<layout>.png)')
    parser.add_argument('--center', '-c', type=str, choices=['single', 'triple_standard', 'triple_expanded', 'diamond_standard', 'diamond_expanded', 'diamond_maximal', 'five_standard', 'random'], 
                        default='random', help='Center hexagon archetype (default: random)')
    parser.add_argument('--numsupply', type=int, default=5,
                        help='Number of supply centers to select (default: 5)')
    parser.add_argument('--supplydist', type=str, choices=['none', 'random', 'oneperhex', 'algo'], 
                        default='none', help='Supply territory distribution: none, random, oneperhex (requires numsupply=7), or algo (min 2-edge distance) (default: none)')
    parser.add_argument('--archetypes', '-a', type=str, choices=['standard_only', 'expanded_only', 'all'], 
                        default='all', help='Archetype types for ring hexagons: standard_only, expanded_only, or all (default: all)')
    args = parser.parse_args()
    
    # Create the hexagon grid
    grid = create_hexagon_ring(args.center, args.archetypes)
    
    # Create supply territories
    supply_territories = create_supply_territories(grid, args.supplydist, args.numsupply)
    
    # Process output filename to ensure it goes to outputs folder
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
        show_touching_sides=args.showsides,
        output_filename=output_filename,
        supply_territories=supply_territories
    )
    
    return grid


if __name__ == "__main__":
    main()