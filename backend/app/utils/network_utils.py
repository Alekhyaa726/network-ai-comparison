"""
Network utility functions.
Helper functions for network operations and data processing.
"""
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

class NetworkUtils:
    """Utility functions for network operations."""
    
    @staticmethod
    def calculate_network_metrics(graph: nx.Graph) -> Dict[str, float]:
        """Calculate comprehensive network metrics."""
        if not graph or len(graph.nodes) == 0:
            return {
                'density': 0.0,
                'avg_clustering': 0.0,
                'avg_path_length': 0.0,
                'diameter': 0.0,
                'efficiency': 0.0,
                'centralization': 0.0
            }
        
        metrics = {}
        
        # Density
        metrics['density'] = nx.density(graph)
        
        # Average clustering coefficient
        try:
            metrics['avg_clustering'] = nx.average_clustering(graph)
        except:
            metrics['avg_clustering'] = 0.0
        
        # Average shortest path length
        try:
            if nx.is_connected(graph):
                metrics['avg_path_length'] = nx.average_shortest_path_length(graph)
                metrics['diameter'] = nx.diameter(graph)
            else:
                # For disconnected graphs, use largest connected component
                largest_cc = max(nx.connected_components(graph), key=len)
                subgraph = graph.subgraph(largest_cc)
                metrics['avg_path_length'] = nx.average_shortest_path_length(subgraph)
                metrics['diameter'] = nx.diameter(subgraph)
        except:
            metrics['avg_path_length'] = 0.0
            metrics['diameter'] = 0.0
        
        # Global efficiency
        try:
            metrics['efficiency'] = nx.global_efficiency(graph)
        except:
            metrics['efficiency'] = 0.0
        
        # Degree centralization
        try:
            degrees = [graph.degree(n) for n in graph.nodes()]
            max_degree = max(degrees)
            n = len(graph.nodes())
            centralization = sum(max_degree - d for d in degrees) / ((n - 1) * (n - 2))
            metrics['centralization'] = centralization
        except:
            metrics['centralization'] = 0.0
        
        return metrics
    
    @staticmethod
    def find_alternative_paths(graph: nx.Graph, source: int, target: int, k: int = 3) -> List[List[int]]:
        """Find k alternative paths between source and target."""
        try:
            paths = list(nx.shortest_simple_paths(graph, source, target))
            return paths[:k]
        except:
            return []
    
    @staticmethod
    def calculate_node_importance(graph: nx.Graph) -> Dict[int, float]:
        """Calculate importance score for each node."""
        importance = {}
        
        try:
            # Betweenness centrality
            betweenness = nx.betweenness_centrality(graph)
            
            # Degree centrality
            degree_centrality = nx.degree_centrality(graph)
            
            # Closeness centrality
            closeness = nx.closeness_centrality(graph)
            
            # Combined importance score
            for node in graph.nodes():
                importance[node] = (
                    betweenness.get(node, 0) * 0.4 +
                    degree_centrality.get(node, 0) * 0.3 +
                    closeness.get(node, 0) * 0.3
                )
        except:
            # Fallback to degree-based importance
            for node in graph.nodes():
                importance[node] = graph.degree(node) / len(graph.nodes())
        
        return importance
    
    @staticmethod
    def simulate_traffic_flow(graph: nx.Graph, flow_matrix: np.ndarray) -> Dict[str, float]:
        """Simulate traffic flow through the network."""
        if not graph or flow_matrix.size == 0:
            return {}
        
        flow_results = {}
        nodes = list(graph.nodes())
        
        try:
            # Calculate flow for each edge
            for src, dst in graph.edges():
                src_idx = nodes.index(src)
                dst_idx = nodes.index(dst)
                
                # Sum traffic from flow matrix
                edge_flow = flow_matrix[src_idx, dst_idx] + flow_matrix[dst_idx, src_idx]
                edge_capacity = graph.edges[src, dst].get('capacity', 45)
                
                utilization = edge_flow / edge_capacity if edge_capacity > 0 else 0
                flow_results[f"{src}-{dst}"] = {
                    'flow': edge_flow,
                    'capacity': edge_capacity,
                    'utilization': min(1.0, utilization)
                }
        except:
            pass
        
        return flow_results
    
    @staticmethod
    def detect_network_bottlenecks(graph: nx.Graph, utilization_threshold: float = 0.8) -> List[Tuple[int, int]]:
        """Detect network bottlenecks based on utilization."""
        bottlenecks = []
        
        for src, dst in graph.edges():
            edge_data = graph.edges[src, dst]
            utilization = edge_data.get('utilization', 0)
            
            if utilization >= utilization_threshold:
                bottlenecks.append((src, dst))
        
        return bottlenecks
    
    @staticmethod
    def calculate_network_resilience(graph: nx.Graph) -> float:
        """Calculate network resilience to failures."""
        if not graph or len(graph.nodes()) <= 1:
            return 0.0
        
        original_connectivity = nx.node_connectivity(graph) if nx.is_connected(graph) else 0
        
        # Test resilience by removing nodes
        resilience_scores = []
        nodes = list(graph.nodes())
        
        for node in nodes:
            temp_graph = graph.copy()
            temp_graph.remove_node(node)
            
            if len(temp_graph.nodes()) > 0:
                if nx.is_connected(temp_graph):
                    new_connectivity = nx.node_connectivity(temp_graph)
                    resilience = new_connectivity / max(1, original_connectivity)
                else:
                    # Disconnected graph
                    largest_cc = max(nx.connected_components(temp_graph), key=len)
                    resilience = len(largest_cc) / len(nodes)
            else:
                resilience = 0.0
            
            resilience_scores.append(resilience)
        
        return np.mean(resilience_scores) if resilience_scores else 0.0
    
    @staticmethod
    def generate_traffic_matrix(num_nodes: int, traffic_pattern: str = 'uniform') -> np.ndarray:
        """Generate traffic matrix for simulation."""
        matrix = np.zeros((num_nodes, num_nodes))
        
        if traffic_pattern == 'uniform':
            # Uniform random traffic
            matrix = np.random.uniform(0, 10, (num_nodes, num_nodes))
            np.fill_diagonal(matrix, 0)  # No self-traffic
        
        elif traffic_pattern == 'gravity':
            # Gravity model (larger nodes attract more traffic)
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if i != j:
                        # Simple gravity model
                        traffic = np.random.exponential(5) * (i + 1) * (j + 1) / (abs(i - j) + 1)
                        matrix[i, j] = traffic
        
        elif traffic_pattern == 'hotspot':
            # Hotspot traffic (some nodes are heavily used)
            hotspots = np.random.choice(num_nodes, size=max(1, num_nodes // 4), replace=False)
            
            for i in range(num_nodes):
                for j in range(num_nodes):
                    if i != j:
                        base_traffic = np.random.uniform(0, 2)
                        if i in hotspots or j in hotspots:
                            base_traffic *= 5
                        matrix[i, j] = base_traffic
        
        return matrix
    
    @staticmethod
    def convert_to_visualization_format(graph: nx.Graph, positions: Optional[Dict[int, Tuple[float, float]]] = None) -> Dict[str, Any]:
        """Convert NetworkX graph to format suitable for D3.js visualization."""
        if positions is None:
            positions = nx.spring_layout(graph)
        
        # Convert nodes
        nodes = []
        for node_id in graph.nodes():
            node_data = graph.nodes[node_id]
            pos = positions.get(node_id, (0, 0))
            
            nodes.append({
                'id': node_id,
                'name': node_data.get('name', f'Node {node_id}'),
                'x': pos[0] * 500 + 250,  # Scale for visualization
                'y': pos[1] * 400 + 200,
                'type': node_data.get('type', 'backbone'),
                'status': node_data.get('status', 'active'),
                'utilization': node_data.get('utilization', 0.0),
                'response_time': node_data.get('response_time', 10.0)
            })
        
        # Convert edges
        links = []
        for src, dst in graph.edges():
            edge_data = graph.edges[src, dst]
            
            links.append({
                'source': src,
                'target': dst,
                'capacity': edge_data.get('capacity', 45),
                'delay': edge_data.get('delay', 20),
                'cost': edge_data.get('cost', 1),
                'status': edge_data.get('status', 'active'),
                'utilization': edge_data.get('utilization', 0.0),
                'packet_loss': edge_data.get('packet_loss', 0.0),
                'latency': edge_data.get('latency', 20.0)
            })
        
        return {
            'nodes': nodes,
            'links': links,
            'metadata': {
                'node_count': len(nodes),
                'link_count': len(links),
                'is_connected': nx.is_connected(graph) if graph else False
            }
        }