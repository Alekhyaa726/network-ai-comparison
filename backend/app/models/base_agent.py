"""
Base agent class for network AI models.
Provides common interface and functionality for all AI agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
import time
import logging
from enum import Enum

class ActionType(Enum):
    MAINTAIN = "maintain"
    REROUTE = "reroute_traffic"
    BACKUP_LINK = "activate_backup_link"
    EMERGENCY_REROUTE = "emergency_reroute"
    LOAD_BALANCE = "load_balance"
    ERROR_CORRECTION = "error_correction"
    CLUSTER_REROUTE = "cluster_reroute"
    BACKUP_ACTIVATION = "backup_activation"
    TRAFFIC_SHAPING = "traffic_shaping"
    PRIMARY_REROUTE = "primary_reroute"
    FULL_REROUTE = "full_reroute"
    SECONDARY_PATH = "secondary_path"
    RETRANSMISSION = "retransmission"
    QOS_ADJUSTMENT = "qos_adjustment"

class FaultType(Enum):
    NONE = "none"
    NODE_DOWN = "node_down"
    LINK_DOWN = "link_down"
    CONGESTION = "congestion"
    PACKET_LOSS = "packet_loss"
    CASCADING = "cascading_failure"

class NetworkState(Enum):
    NORMAL = "normal"
    DEGRADED = "degraded"
    CRITICAL = "critical"

class BaseAgent(ABC):
    """Base class for all network AI agents."""
    
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.decision_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {
            "healing_time": 0.0,
            "recovery_accuracy": 0.0,
            "decision_count": 0.0,
            "success_rate": 0.0
        }
        self.is_active = False
        self.last_decision_time = 0.0
    
    @abstractmethod
    def detect_fault(self, network_state: Dict[str, Any]) -> Tuple[FaultType, Optional[str]]:
        """
        Detect faults in the network state.
        
        Args:
            network_state: Current state of the network
            
        Returns:
            Tuple of (fault_type, fault_location)
        """
        pass
    
    @abstractmethod
    def decide_action(self, network_state: Dict[str, Any], fault_info: Tuple[FaultType, Optional[str]]) -> ActionType:
        """
        Decide on the best action to take given the network state and fault.
        
        Args:
            network_state: Current state of the network
            fault_info: Detected fault information
            
        Returns:
            ActionType to execute
        """
        pass
    
    @abstractmethod
    def execute_healing(self, action: ActionType, network: Any, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """
        Execute the healing action on the network.
        
        Args:
            action: Action to execute
            network: Network object to modify
            fault_info: Fault information
            
        Returns:
            Dictionary containing execution results
        """
        pass
    
    def process_network_event(self, network_state: Dict[str, Any], network: Any) -> Dict[str, Any]:
        """
        Main processing method that coordinates fault detection, decision making, and healing.
        
        Args:
            network_state: Current network state
            network: Network object
            
        Returns:
            Dictionary containing processing results
        """
        start_time = time.time()
        
        # Detect fault
        fault_type, fault_location = self.detect_fault(network_state)
        
        # Decide action
        action = self.decide_action(network_state, (fault_type, fault_location))
        
        # Execute healing
        result = self.execute_healing(action, network, (fault_type, fault_location))
        
        # Record decision
        decision_time = time.time() - start_time
        decision_record = {
            "timestamp": time.time(),
            "agent_id": self.agent_id,
            "fault_type": fault_type.value,
            "fault_location": fault_location,
            "action": action.value,
            "decision_time": decision_time,
            "result": result
        }
        
        self.decision_history.append(decision_record)
        self.last_decision_time = decision_time
        self.performance_metrics["decision_count"] += 1
        
        # Update performance metrics
        if result.get("success", False):
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["success_rate"] * (self.performance_metrics["decision_count"] - 1) + 1
            ) / self.performance_metrics["decision_count"]
        else:
            self.performance_metrics["success_rate"] = (
                self.performance_metrics["success_rate"] * (self.performance_metrics["decision_count"] - 1)
            ) / self.performance_metrics["decision_count"]
        
        self.logger.info(f"Processed event: {fault_type.value} -> {action.value} (time: {decision_time:.3f}s)")
        
        return decision_record
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get current performance metrics."""
        return self.performance_metrics.copy()
    
    def get_recent_decisions(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent decision history."""
        return self.decision_history[-count:] if self.decision_history else []
    
    def reset_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            "healing_time": 0.0,
            "recovery_accuracy": 0.0,
            "decision_count": 0.0,
            "success_rate": 0.0
        }
        self.decision_history.clear()
    
    def activate(self):
        """Activate the agent."""
        self.is_active = True
        self.logger.info(f"Agent {self.name} activated")
    
    def deactivate(self):
        """Deactivate the agent."""
        self.is_active = False
        self.logger.info(f"Agent {self.name} deactivated")