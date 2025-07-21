"""
Network Manager for handling network topology and state management.
Manages NSFNET topology and provides network state information.
"""
import json
import networkx as nx
import numpy as np
import time
from typing import Dict, List, Any, Tuple, Optional
import logging
from pathlib import Path

class NetworkManager:
    """Manages network topology and state for simulation."""
    
    def __init__(self, topology_path: str = "/app/data/nsfnet_topology.json"):
        self.logger = logging.getLogger("network_manager")
        self.topology_path = topology_path
        self.base_topology = None
        self.networks = {}  # Store separate network instances for each AI agent
        self.network_states = {}
        self.topology_data = None
        
        # Load base topology
        self._load_topology()
        
        # Initialize networks for each AI agent
        self._initialize_agent_networks()
    
    def _load_topology(self):
        """Load NSFNET topology from JSON file."""
        try:
            if Path(self.topology_path).exists():
                with open(self.topology_path, 'r') as f:
                    self.topology_data = json.load(f)
                
                # Create NetworkX graph
                self.base_topology = nx.Graph()
                
                # Add nodes
                for node in self.topology_data['nodes']:
                    self.base_topology.add_node(
                        node['id'],
                        name=node['name'],
                        x=node['x'],
                        y=node['y'],
                        type=node['type'],
                        status='active',
                        utilization=0.0,
                        response_time=10.0
                    )
                
                # Add edges
                for link in self.topology_data['links']:
                    self.base_topology.add_edge(
                        link['source'],
                        link['target'],
                        capacity=link['capacity'],
                        delay=link['delay'],
                        cost=link['cost'],
                        status='active',
                        utilization=0.0,
                        packet_loss=0.0,
                        latency=link['delay']
                    )
                
                self.logger.info(f"Loaded topology: {len(self.base_topology.nodes)} nodes, {len(self.base_topology.edges)} edges")
                
            else:
                self.logger.error(f"Topology file not found: {self.topology_path}")
                self._create_default_topology()
                
        except Exception as e:
            self.logger.error(f"Failed to load topology: {str(e)}")
            self._create_default_topology()
    
    def _create_default_topology(self):
        """Create a default NSFNET topology if file loading fails."""
        self.logger.info("Creating default NSFNET topology")
        
        self.base_topology = nx.Graph()
        
        # Default NSFNET nodes
        nodes = [
            (0, "Seattle", 50, 100), (1, "Palo Alto", 50, 200),
            (2, "Salt Lake City", 150, 120), (3, "Boulder", 200, 150),
            (4, "Lincoln", 250, 170), (5, "Houston", 230, 250),
            (6, "Atlanta", 350, 220), (7, "Pittsburgh", 380, 150),
            (8, "Ithaca", 400, 120), (9, "Princeton", 420, 140),
            (10, "Cambridge", 450, 100), (11, "Ann Arbor", 330, 120),
            (12, "Champaign", 300, 160), (13, "San Diego", 70, 270)
        ]
        
        for node_id, name, x, y in nodes:
            self.base_topology.add_node(
                node_id, name=name, x=x, y=y, type="backbone",
                status='active', utilization=0.0, response_time=10.0
            )
        
        # Default NSFNET links
        links = [
            (0, 1), (0, 2), (1, 2), (1, 13), (2, 3), (3, 4), (3, 5), (3, 11),
            (4, 5), (4, 12), (5, 6), (6, 7), (7, 8), (7, 11), (8, 9), 
            (8, 10), (9, 10), (11, 12)
        ]
        
        for src, dst in links:
            self.base_topology.add_edge(
                src, dst, capacity=45, delay=20, cost=1,
                status='active', utilization=0.0, packet_loss=0.0, latency=20
            )
    
    def _initialize_agent_networks(self):
        """Initialize separate network instances for each AI agent."""
        agent_ids = ['rule_based', 'regression', 'rl']
        
        for agent_id in agent_ids:
            # Create deep copy of base topology
            self.networks[agent_id] = self.base_topology.copy()
            self.network_states[agent_id] = self._create_initial_state()
            
            self.logger.info(f"Initialized network for agent: {agent_id}")
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """Create initial network state."""
        return {
            'timestamp': time.time(),
            'throughput': 100.0,
            'latency': 10.0,
            'packet_loss': 0.0,
            'connectivity': 1.0,
            'active_nodes': len(self.base_topology.nodes),
            'active_links': len(self.base_topology.edges),
            'network_state': 'normal',
            'node_states': {},
            'link_states': {},
            'faults': []
        }
    
    def get_network(self, agent_id: str) -> nx.Graph:
        """Get network instance for specific agent."""
        return self.networks.get(agent_id)
    
    def get_network_state(self, agent_id: str) -> Dict[str, Any]:
        """Get current network state for specific agent."""
        if agent_id in self.networks:
            return self._compute_current_state(agent_id)
        return None
    
    def _compute_current_state(self, agent_id: str) -> Dict[str, Any]:
        """Compute current network state from topology."""
        network = self.networks[agent_id]
        state = self.network_states[agent_id].copy()
        
        # Update timestamp
        state['timestamp'] = time.time()
        
        # Compute node states
        node_states = {}
        total_utilization = 0
        total_response_time = 0
        active_nodes = 0
        
        for node_id in network.nodes():
            node_data = network.nodes[node_id]
            node_state = {
                'status': node_data.get('status', 'active'),
                'utilization': node_data.get('utilization', 0.0),
                'response_time': node_data.get('response_time', 10.0)
            }
            node_states[str(node_id)] = node_state
            
            if node_state['status'] == 'active':
                active_nodes += 1
                total_utilization += node_state['utilization']
                total_response_time += node_state['response_time']
        
        state['node_states'] = node_states
        state['active_nodes'] = active_nodes
        
        # Compute link states
        link_states = {}
        total_link_utilization = 0
        total_link_latency = 0
        total_packet_loss = 0
        active_links = 0
        
        for src, dst in network.edges():
            edge_data = network.edges[src, dst]
            link_id = f"{src}-{dst}"
            link_state = {
                'status': edge_data.get('status', 'active'),
                'utilization': edge_data.get('utilization', 0.0),
                'latency': edge_data.get('latency', 20.0),
                'packet_loss': edge_data.get('packet_loss', 0.0),
                'capacity': edge_data.get('capacity', 45)
            }
            link_states[link_id] = link_state
            
            if link_state['status'] == 'active':
                active_links += 1
                total_link_utilization += link_state['utilization']
                total_link_latency += link_state['latency']
                total_packet_loss += link_state['packet_loss']
        
        state['link_states'] = link_states
        state['active_links'] = active_links
        
        # Compute aggregate metrics
        if active_nodes > 0:
            avg_utilization = total_utilization / active_nodes
            avg_response_time = total_response_time / active_nodes
            state['throughput'] = max(0, 100 - avg_utilization * 50)
        else:
            state['throughput'] = 0
        
        if active_links > 0:
            avg_link_latency = total_link_latency / active_links
            avg_packet_loss = total_packet_loss / active_links
            state['latency'] = avg_link_latency
            state['packet_loss'] = avg_packet_loss
        else:
            state['latency'] = 1000
            state['packet_loss'] = 1.0
        
        # Compute connectivity
        if active_nodes > 1:
            try:
                # Check if network is connected
                largest_cc = max(nx.connected_components(network), key=len)
                state['connectivity'] = len(largest_cc) / len(network.nodes)
            except:
                state['connectivity'] = 0.0
        else:
            state['connectivity'] = 0.0
        
        # Determine overall network state
        if state['connectivity'] < 0.7 or state['throughput'] < 50:
            state['network_state'] = 'critical'
        elif state['connectivity'] < 0.9 or state['throughput'] < 80:
            state['network_state'] = 'degraded'
        else:
            state['network_state'] = 'normal'
        
        return state
    
    def apply_fault(self, agent_id: str, fault_type: str, target: Any):
        """Apply fault to specific agent's network."""
        if agent_id not in self.networks:
            return False
        
        network = self.networks[agent_id]
        
        try:
            if fault_type == 'node_down':
                self._apply_node_fault(network, target)
            elif fault_type == 'link_down':
                self._apply_link_fault(network, target)
            elif fault_type == 'congestion':
                self._apply_congestion_fault(network, target)
            elif fault_type == 'packet_loss':
                self._apply_packet_loss_fault(network, target)
            elif fault_type == 'cascading':
                self._apply_cascading_fault(network, target)
            
            # Update network state
            self.network_states[agent_id] = self._compute_current_state(agent_id)
            
            # Record fault
            fault_record = {
                'timestamp': time.time(),
                'type': fault_type,
                'target': str(target),
                'agent_id': agent_id
            }
            self.network_states[agent_id]['faults'].append(fault_record)
            
            self.logger.info(f"Applied fault {fault_type} to {target} for agent {agent_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply fault: {str(e)}")
            return False
    
    def _apply_node_fault(self, network: nx.Graph, node_id: int):
        """Apply node failure."""
        if node_id in network.nodes:
            network.nodes[node_id]['status'] = 'down'
            network.nodes[node_id]['utilization'] = 0.0
            network.nodes[node_id]['response_time'] = float('inf')
    
    def _apply_link_fault(self, network: nx.Graph, link_spec: str):
        """Apply link failure."""
        if '-' in str(link_spec):
            try:
                src, dst = map(int, str(link_spec).split('-'))
                if network.has_edge(src, dst):
                    network.edges[src, dst]['status'] = 'down'
                    network.edges[src, dst]['utilization'] = 0.0
                    network.edges[src, dst]['packet_loss'] = 1.0
                    network.edges[src, dst]['latency'] = float('inf')
            except ValueError:
                pass
    
    def _apply_congestion_fault(self, network: nx.Graph, node_id: int):
        """Apply congestion to a node."""
        if node_id in network.nodes:
            network.nodes[node_id]['utilization'] = min(1.0, network.nodes[node_id].get('utilization', 0) + 0.6)
            network.nodes[node_id]['response_time'] = network.nodes[node_id].get('response_time', 10) * 3
            
            # Affect neighboring links
            for neighbor in network.neighbors(node_id):
                if network.has_edge(node_id, neighbor):
                    edge_data = network.edges[node_id, neighbor]
                    edge_data['utilization'] = min(1.0, edge_data.get('utilization', 0) + 0.4)
                    edge_data['latency'] = edge_data.get('latency', 20) * 2
    
    def _apply_packet_loss_fault(self, network: nx.Graph, target: str):
        """Apply packet loss to network."""
        # Apply to random links
        edges = list(network.edges())
        affected_edges = np.random.choice(len(edges), size=min(3, len(edges)), replace=False)
        
        for edge_idx in affected_edges:
            src, dst = edges[edge_idx]
            network.edges[src, dst]['packet_loss'] = min(1.0, 
                network.edges[src, dst].get('packet_loss', 0) + np.random.uniform(0.1, 0.3))
    
    def _apply_cascading_fault(self, network: nx.Graph, target: str):
        """Apply cascading failure."""
        # Start with random node failure
        nodes = list(network.nodes())
        initial_node = np.random.choice(nodes)
        self._apply_node_fault(network, initial_node)
        
        # Cascade to neighbors with probability
        affected_nodes = {initial_node}
        cascade_prob = 0.3
        
        for _ in range(3):  # Max 3 cascade levels
            new_affected = set()
            for node in affected_nodes:
                if node in network.nodes:
                    for neighbor in network.neighbors(node):
                        if neighbor not in affected_nodes and np.random.random() < cascade_prob:
                            self._apply_node_fault(network, neighbor)
                            new_affected.add(neighbor)
            
            if not new_affected:
                break
            affected_nodes.update(new_affected)
            cascade_prob *= 0.7  # Decrease probability with each level
    
    def heal_network(self, agent_id: str, healing_result: Dict[str, Any]):
        """Apply healing result to network."""
        if agent_id not in self.networks:
            return False
        
        network = self.networks[agent_id]
        
        try:
            if healing_result.get('success', False):
                # Apply healing improvements
                changes = healing_result.get('changes', [])
                
                # Simulate healing by reducing fault severity
                for node_id in network.nodes():
                    node_data = network.nodes[node_id]
                    if node_data.get('status') == 'down' and np.random.random() < 0.3:
                        # Chance to restore node
                        node_data['status'] = 'active'
                        node_data['utilization'] = 0.2
                        node_data['response_time'] = 15.0
                    elif node_data.get('utilization', 0) > 0.8:
                        # Reduce congestion
                        node_data['utilization'] *= 0.8
                        node_data['response_time'] *= 0.9
                
                for src, dst in network.edges():
                    edge_data = network.edges[src, dst]
                    if edge_data.get('status') == 'down' and np.random.random() < 0.4:
                        # Chance to restore link
                        edge_data['status'] = 'active'
                        edge_data['utilization'] = 0.1
                        edge_data['packet_loss'] = 0.0
                        edge_data['latency'] = edge_data.get('delay', 20)
                    elif edge_data.get('packet_loss', 0) > 0.1:
                        # Reduce packet loss
                        edge_data['packet_loss'] *= 0.7
                    
                    if edge_data.get('utilization', 0) > 0.7:
                        # Reduce utilization
                        edge_data['utilization'] *= 0.8
                        edge_data['latency'] *= 0.9
            
            # Update network state
            self.network_states[agent_id] = self._compute_current_state(agent_id)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply healing: {str(e)}")
            return False
    
    def reset_network(self, agent_id: str):
        """Reset network to initial state."""
        if agent_id in self.networks:
            self.networks[agent_id] = self.base_topology.copy()
            self.network_states[agent_id] = self._create_initial_state()
            self.logger.info(f"Reset network for agent: {agent_id}")
    
    def reset_all_networks(self):
        """Reset all agent networks to initial state."""
        for agent_id in self.networks.keys():
            self.reset_network(agent_id)
        self.logger.info("Reset all networks")
    
    def get_topology_data(self) -> Dict[str, Any]:
        """Get original topology data for visualization."""
        return self.topology_data
    
    def get_network_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all networks."""
        stats = {}
        for agent_id in self.networks:
            state = self.get_network_state(agent_id)
            stats[agent_id] = {
                'nodes': len(self.networks[agent_id].nodes),
                'edges': len(self.networks[agent_id].edges),
                'active_nodes': state.get('active_nodes', 0),
                'active_links': state.get('active_links', 0),
                'connectivity': state.get('connectivity', 0),
                'throughput': state.get('throughput', 0),
                'latency': state.get('latency', 0),
                'network_state': state.get('network_state', 'unknown')
            }
        return stats