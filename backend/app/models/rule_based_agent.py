"""
Rule-Based Expert System for network self-healing.
Uses predefined expert rules to make decisions about network fault recovery.
"""
from typing import Dict, List, Any, Optional, Tuple
import time
import networkx as nx
from .base_agent import BaseAgent, ActionType, FaultType, NetworkState

class RuleBasedAgent(BaseAgent):
    """Expert system agent using rule-based decision making."""
    
    def __init__(self):
        super().__init__("rule_based", "Rule-Based Expert System")
        self.rules = self._load_expert_rules()
        self.confidence_threshold = 0.8
        self.decision_tree = self._build_decision_tree()
    
    def _load_expert_rules(self) -> Dict[str, Any]:
        """Load expert rules for network healing."""
        return {
            "fault_detection": {
                "node_down_indicators": ["zero_throughput", "no_response", "connection_timeout"],
                "link_down_indicators": ["packet_loss_100", "routing_failure", "no_connectivity"],
                "congestion_indicators": ["high_latency", "packet_loss_partial", "throughput_degraded"],
                "cascading_indicators": ["multiple_failures", "propagating_errors", "system_instability"]
            },
            "healing_strategies": {
                FaultType.NODE_DOWN: {
                    "primary": ActionType.CLUSTER_REROUTE,
                    "secondary": ActionType.PRIMARY_REROUTE,
                    "emergency": ActionType.EMERGENCY_REROUTE
                },
                FaultType.LINK_DOWN: {
                    "primary": ActionType.BACKUP_ACTIVATION,
                    "secondary": ActionType.SECONDARY_PATH,
                    "emergency": ActionType.REROUTE
                },
                FaultType.CONGESTION: {
                    "primary": ActionType.LOAD_BALANCE,
                    "secondary": ActionType.TRAFFIC_SHAPING,
                    "emergency": ActionType.QOS_ADJUSTMENT
                },
                FaultType.PACKET_LOSS: {
                    "primary": ActionType.ERROR_CORRECTION,
                    "secondary": ActionType.RETRANSMISSION,
                    "emergency": ActionType.REROUTE
                },
                FaultType.CASCADING: {
                    "primary": ActionType.EMERGENCY_REROUTE,
                    "secondary": ActionType.FULL_REROUTE,
                    "emergency": ActionType.CLUSTER_REROUTE
                }
            },
            "priority_matrix": {
                NetworkState.CRITICAL: "emergency",
                NetworkState.DEGRADED: "primary", 
                NetworkState.NORMAL: "secondary"
            }
        }
    
    def _build_decision_tree(self) -> Dict[str, Any]:
        """Build decision tree for rule evaluation."""
        return {
            "root": {
                "condition": "network_state_assessment",
                "branches": {
                    NetworkState.CRITICAL: {
                        "action": "emergency_response",
                        "confidence": 0.95
                    },
                    NetworkState.DEGRADED: {
                        "action": "standard_response", 
                        "confidence": 0.85
                    },
                    NetworkState.NORMAL: {
                        "action": "preventive_response",
                        "confidence": 0.75
                    }
                }
            }
        }
    
    def detect_fault(self, network_state: Dict[str, Any]) -> Tuple[FaultType, Optional[str]]:
        """
        Rule-based fault detection using expert knowledge.
        
        Args:
            network_state: Current network state with metrics
            
        Returns:
            Tuple of (fault_type, fault_location)
        """
        # Extract key metrics
        throughput = network_state.get("throughput", 100)
        latency = network_state.get("latency", 10)
        packet_loss = network_state.get("packet_loss", 0)
        node_states = network_state.get("node_states", {})
        link_states = network_state.get("link_states", {})
        
        # Rule 1: Node failure detection
        for node_id, state in node_states.items():
            if state.get("status") == "down" or state.get("response_time", 0) > 1000:
                return FaultType.NODE_DOWN, str(node_id)
        
        # Rule 2: Link failure detection  
        for link_id, state in link_states.items():
            if state.get("status") == "down" or state.get("packet_loss", 0) >= 1.0:
                return FaultType.LINK_DOWN, str(link_id)
        
        # Rule 3: Congestion detection
        if latency > 50 and throughput < 70:
            congested_nodes = [node for node, state in node_states.items() 
                             if state.get("utilization", 0) > 0.8]
            if congested_nodes:
                return FaultType.CONGESTION, str(congested_nodes[0])
        
        # Rule 4: Packet loss detection
        if 0 < packet_loss < 1.0 and throughput > 70:
            return FaultType.PACKET_LOSS, "network_wide"
        
        # Rule 5: Cascading failure detection
        failed_components = sum(1 for state in list(node_states.values()) + list(link_states.values())
                              if state.get("status") == "down")
        if failed_components >= 3:
            return FaultType.CASCADING, "multiple"
        
        return FaultType.NONE, None
    
    def decide_action(self, network_state: Dict[str, Any], fault_info: Tuple[FaultType, Optional[str]]) -> ActionType:
        """
        Rule-based action decision using expert strategies.
        
        Args:
            network_state: Current network state
            fault_info: Detected fault information
            
        Returns:
            ActionType to execute
        """
        fault_type, fault_location = fault_info
        
        if fault_type == FaultType.NONE:
            return ActionType.MAINTAIN
        
        # Assess network criticality
        network_criticality = self._assess_network_criticality(network_state)
        
        # Get healing strategies for fault type
        strategies = self.rules["healing_strategies"].get(fault_type, {})
        priority = self.rules["priority_matrix"].get(network_criticality, "primary")
        
        # Select action based on priority and fault type
        action = strategies.get(priority, ActionType.MAINTAIN)
        
        # Apply additional rules based on context
        if fault_location and self._is_critical_component(fault_location, network_state):
            # Escalate action for critical components
            if priority == "primary":
                action = strategies.get("emergency", action)
            elif priority == "secondary":
                action = strategies.get("primary", action)
        
        self.logger.info(f"Rule decision: {fault_type.value} at {fault_location} -> {action.value} (priority: {priority})")
        return action
    
    def execute_healing(self, action: ActionType, network: Any, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """
        Execute healing action using rule-based approach.
        
        Args:
            action: Action to execute
            network: NetworkX graph object
            fault_info: Fault information
            
        Returns:
            Execution results
        """
        fault_type, fault_location = fault_info
        execution_start = time.time()
        
        try:
            result = {"success": False, "message": "", "changes": []}
            
            if action == ActionType.MAINTAIN:
                result["success"] = True
                result["message"] = "Network maintained in current state"
            
            elif action == ActionType.CLUSTER_REROUTE:
                result = self._execute_cluster_reroute(network, fault_location)
            
            elif action == ActionType.BACKUP_ACTIVATION:
                result = self._execute_backup_activation(network, fault_location)
            
            elif action == ActionType.LOAD_BALANCE:
                result = self._execute_load_balancing(network, fault_location)
            
            elif action == ActionType.EMERGENCY_REROUTE:
                result = self._execute_emergency_reroute(network)
            
            elif action == ActionType.ERROR_CORRECTION:
                result = self._execute_error_correction(network)
            
            else:
                result = self._execute_generic_healing(network, action, fault_location)
            
            execution_time = time.time() - execution_start
            result["execution_time"] = execution_time
            
            self.performance_metrics["healing_time"] = (
                self.performance_metrics["healing_time"] + execution_time
            ) / max(1, self.performance_metrics["decision_count"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Healing execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Execution failed: {str(e)}",
                "execution_time": time.time() - execution_start,
                "changes": []
            }
    
    def _assess_network_criticality(self, network_state: Dict[str, Any]) -> NetworkState:
        """Assess overall network criticality using rules."""
        throughput = network_state.get("throughput", 100)
        connectivity = network_state.get("connectivity", 1.0)
        active_nodes = network_state.get("active_nodes", 14)
        
        # Critical state rules
        if throughput < 50 or connectivity < 0.7 or active_nodes < 10:
            return NetworkState.CRITICAL
        
        # Degraded state rules  
        if throughput < 80 or connectivity < 0.9 or active_nodes < 12:
            return NetworkState.DEGRADED
        
        return NetworkState.NORMAL
    
    def _is_critical_component(self, component_id: str, network_state: Dict[str, Any]) -> bool:
        """Determine if a component is critical based on rules."""
        # Rule: Core backbone nodes are critical
        backbone_nodes = ["5", "6", "7", "11", "12"]  # Central NSFNET nodes
        
        if component_id in backbone_nodes:
            return True
        
        # Rule: High-traffic links are critical
        link_states = network_state.get("link_states", {})
        if component_id in link_states:
            utilization = link_states[component_id].get("utilization", 0)
            if utilization > 0.7:
                return True
        
        return False
    
    def _execute_cluster_reroute(self, network: nx.Graph, fault_location: str) -> Dict[str, Any]:
        """Execute cluster-based rerouting around failed node."""
        changes = []
        try:
            if fault_location and fault_location.isdigit():
                node = int(fault_location)
                if node in network:
                    # Find alternative paths through neighboring clusters
                    neighbors = list(network.neighbors(node))
                    for neighbor in neighbors:
                        # Redirect traffic through neighbor clusters
                        changes.append(f"Rerouted traffic from node {node} through cluster at {neighbor}")
                    
                    return {
                        "success": True,
                        "message": f"Cluster rerouting completed for node {node}",
                        "changes": changes
                    }
            
            return {"success": False, "message": "Invalid node for cluster rerouting", "changes": []}
        except Exception as e:
            return {"success": False, "message": f"Cluster rerouting failed: {str(e)}", "changes": changes}
    
    def _execute_backup_activation(self, network: nx.Graph, fault_location: str) -> Dict[str, Any]:
        """Activate backup links/paths."""
        changes = []
        try:
            if "-" in fault_location:  # Link failure
                nodes = fault_location.split("-")
                if len(nodes) == 2:
                    src, dest = int(nodes[0]), int(nodes[1])
                    # Find alternative path
                    try:
                        path = nx.shortest_path(network, src, dest)
                        changes.append(f"Activated backup path: {' -> '.join(map(str, path))}")
                        return {
                            "success": True,
                            "message": f"Backup path activated for link {fault_location}",
                            "changes": changes
                        }
                    except nx.NetworkXNoPath:
                        return {"success": False, "message": "No backup path available", "changes": []}
            
            return {"success": False, "message": "Invalid link for backup activation", "changes": []}
        except Exception as e:
            return {"success": False, "message": f"Backup activation failed: {str(e)}", "changes": changes}
    
    def _execute_load_balancing(self, network: nx.Graph, fault_location: str) -> Dict[str, Any]:
        """Execute load balancing to relieve congestion."""
        changes = []
        try:
            if fault_location and fault_location.isdigit():
                node = int(fault_location)
                neighbors = list(network.neighbors(node))
                # Distribute load among neighbors
                load_per_neighbor = 1.0 / len(neighbors) if neighbors else 0
                for neighbor in neighbors:
                    changes.append(f"Redistributed load to node {neighbor}: {load_per_neighbor:.2f}")
                
                return {
                    "success": True,
                    "message": f"Load balancing completed for node {node}",
                    "changes": changes
                }
            
            return {"success": False, "message": "Invalid node for load balancing", "changes": []}
        except Exception as e:
            return {"success": False, "message": f"Load balancing failed: {str(e)}", "changes": changes}
    
    def _execute_emergency_reroute(self, network: nx.Graph) -> Dict[str, Any]:
        """Execute emergency network-wide rerouting."""
        changes = ["Emergency rerouting protocol activated"]
        try:
            # Find all critical paths and establish emergency routes
            nodes = list(network.nodes())
            for i in range(0, len(nodes), 2):
                if i + 1 < len(nodes):
                    try:
                        path = nx.shortest_path(network, nodes[i], nodes[i+1])
                        changes.append(f"Emergency route: {' -> '.join(map(str, path))}")
                    except nx.NetworkXNoPath:
                        continue
            
            return {
                "success": True,
                "message": "Emergency rerouting completed",
                "changes": changes
            }
        except Exception as e:
            return {"success": False, "message": f"Emergency rerouting failed: {str(e)}", "changes": changes}
    
    def _execute_error_correction(self, network: nx.Graph) -> Dict[str, Any]:
        """Execute error correction protocols."""
        return {
            "success": True,
            "message": "Error correction protocols activated",
            "changes": ["Forward Error Correction enabled", "Retransmission timeouts adjusted"]
        }
    
    def _execute_generic_healing(self, network: nx.Graph, action: ActionType, fault_location: str) -> Dict[str, Any]:
        """Execute generic healing action."""
        return {
            "success": True,
            "message": f"Generic healing action {action.value} executed",
            "changes": [f"Applied {action.value} to {fault_location or 'network'}"]
        }