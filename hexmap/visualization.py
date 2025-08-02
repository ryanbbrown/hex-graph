"""
Territory graph visualization and plotting functionality
"""

from typing import List, Optional
import networkx as nx
import matplotlib.pyplot as plt

from .grid import HexagonGrid


class TerritoryVisualizer:
    """Handles visualization of territory graphs using matplotlib and networkx"""
    
    def __init__(self, grid: HexagonGrid):
        self.grid = grid
    
    def visualize_territory_graph(self, graph: nx.Graph, use_colors: bool = False, 
                                show_ids: bool = False, output_filename: str = None, 
                                supply_territories: List[str] = None):
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
            
            for i, hexagon in enumerate(self.grid.hexagons):
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
        
        # Draw edges first
        nx.draw_networkx_edges(graph, pos, edgelist=internal_edges, edge_color='black', width=2, alpha=0.6)
        nx.draw_networkx_edges(graph, pos, edgelist=inter_edges, edge_color='red', width=3, alpha=0.8, style='dashed')
        
        # Draw regular nodes first
        regular_nodes = [node for node in graph.nodes() if supply_territories is None or node not in supply_territories]
        if regular_nodes:
            regular_colors = [node_colors[i] for i, node in enumerate(graph.nodes()) if node in regular_nodes]
            regular_pos = {node: pos[node] for node in regular_nodes}
            nx.draw_networkx_nodes(graph, regular_pos, nodelist=regular_nodes, node_color=regular_colors, node_size=4000, alpha=0.8)
        
        # Draw supply nodes with black outline on top
        if supply_territories:
            supply_nodes = [node for node in graph.nodes() if node in supply_territories]
            supply_colors = [node_colors[i] for i, node in enumerate(graph.nodes()) if node in supply_nodes]
            supply_pos = {node: pos[node] for node in supply_nodes}
            # Draw the supply nodes with black edge
            nx.draw_networkx_nodes(graph, supply_pos, nodelist=supply_nodes, node_color=supply_colors, 
                                 node_size=4000, alpha=0.8, edgecolors='black', linewidths=3)
        
        # Add labels with short node IDs if requested
        if show_ids:
            labels = {node: node[:8] for node in graph.nodes()}
            nx.draw_networkx_labels(graph, pos, labels, font_size=8)
        
        plt.title(f"Territory Graph - {layout_used.title()} Layout\n(Black lines: internal connections, Red dashed: inter-hexagon connections)")
        plt.axis('off')
        plt.tight_layout()
        
        # Determine output filename
        if output_filename is None:
            output_filename = f'outputs/territory_graph_{layout_used}.png'
        elif not output_filename.endswith('.png'):
            output_filename += '.png'
        
        # Save the image
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        print(f"Territory graph saved as '{output_filename}' using {layout_used} layout")
        
        # Print some stats
        print(f"Graph has {graph.number_of_nodes()} territories and {graph.number_of_edges()} connections")
        internal_count = len(internal_edges)
        inter_count = len(inter_edges)
        print(f"Internal connections: {internal_count}")
        print(f"Inter-hexagon connections: {inter_count}")
        if supply_territories:
            print(f"Supply territories outlined: {len(supply_territories)}")
    
    def create_and_save_visualization(self, use_colors: bool = False, show_ids: bool = False, 
                                    output_filename: str = None, supply_territories: List[str] = None):
        """Extract territory graph and create visualization in one step"""
        graph = self.grid.extract_territory_graph()
        self.visualize_territory_graph(graph, use_colors, show_ids, output_filename, supply_territories)
        return graph