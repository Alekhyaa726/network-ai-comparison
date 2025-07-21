"""
Fault Injector for network simulation.
Handles manual and automated fault injection across all agent networks simultaneously.
"""
import random
import time
import threading
import json
from typing import Dict, List, Any, Optional, Callable
import logging
from enum import Enum

class FaultInjector:
    """Manages fault injection for network simulation."""
    
    def __init__(self, network_manager, config_path: str = "/app/data/network_configs.json"):
        self.logger = logging.getLogger("fault_injector")
        self.network_manager = network_manager
        self.config_path = config_path
        self.config = {}
        self.is_running = False
        self.auto_injection_thread = None
        self.fault_history = []
        self.injection_callbacks = []
        
        # Fault type definitions
        self.fault_types = {
            'node_down': {
                'name': 'Node Failure',
                'description': 'Complete node failure',
                'severity': 'high',
                'recovery_time_range': [10, 60]
            },
            'link_down': {
                'name': 'Link Failure', 
                'description': 'Link/connection failure',
                'severity': 'medium',
                'recovery_time_range': [5, 30]
            },
            'congestion': {
                'name': 'Network Congestion',
                'description': 'Traffic congestion and overload',
                'severity': 'medium',
                'recovery_time_range': [3, 20]
            },
            'packet_loss': {
                'name': 'Packet Loss',
                'description': 'Random packet loss',
                'severity': 'low',
                'recovery_time_range': [1, 10]
            },
            'cascading': {
                'name': 'Cascading Failure',
                'description': 'Progressive failure propagation',
                'severity': 'critical',
                'recovery_time_range': [30, 120]
            }
        }
        
        # Load configuration
        self._load_config()
        
        # Auto-injection state
        self.auto_injection_interval = self.config.get('simulation_config', {}).get('fault_injection_interval', 30)
        self.auto_fault_probability = self.config.get('simulation_config', {}).get('auto_fault_probability', 0.1)
    
    def _load_config(self):
        """Load fault injection configuration."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            # Update fault types with config data
            if 'fault_types' in self.config:
                for fault_type, config_data in self.config['fault_types'].items():
                    if fault_type in self.fault_types:
                        self.fault_types[fault_type].update(config_data)
            
            self.logger.info("Fault injection configuration loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
            # Use default configuration
            self.config = {
                'simulation_config': {
                    'fault_injection_interval': 30,
                    'auto_fault_probability': 0.1
                }
            }
    
    def inject_manual_fault(self, fault_type: str, target: Any = None, description: str = "") -> Dict[str, Any]:
        """
        Manually inject a fault into all agent networks simultaneously.
        
        Args:
            fault_type: Type of fault to inject
            target: Specific target (node/link) or None for random
            description: Optional description of the fault
            
        Returns:
            Fault injection result
        """
        if fault_type not in self.fault_types:
            return {
                "success": False,
                "message": f"Unknown fault type: {fault_type}",
                "fault_id": None
            }
        
        try:
            # Generate fault ID
            fault_id = f"manual_{int(time.time())}_{len(self.fault_history)}"
            
            # Determine target if not specified
            if target is None:
                target = self._select_random_target(fault_type)
            
            # Apply fault to all agent networks
            results = {}
            agent_ids = ['rule_based', 'regression', 'rl']
            
            for agent_id in agent_ids:
                success = self.network_manager.apply_fault(agent_id, fault_type, target)
                results[agent_id] = success
            
            # Record fault in history
            fault_record = {
                'fault_id': fault_id,
                'timestamp': time.time(),
                'type': fault_type,
                'target': str(target),
                'description': description or f"Manual {self.fault_types[fault_type]['name']}",
                'severity': self.fault_types[fault_type]['severity'],
                'injection_method': 'manual',
                'agents_affected': list(results.keys()),
                'success_per_agent': results,
                'expected_recovery_time': self._estimate_recovery_time(fault_type)
            }
            
            self.fault_history.append(fault_record)
            
            # Notify callbacks
            self._notify_injection_callbacks(fault_record)
            
            success_count = sum(results.values())
            total_agents = len(results)
            
            self.logger.info(f"Manual fault injected: {fault_type} at {target} "
                           f"(success: {success_count}/{total_agents} agents)")
            
            return {
                "success": success_count > 0,
                "message": f"Fault injected to {success_count}/{total_agents} agent networks",
                "fault_id": fault_id,
                "fault_record": fault_record
            }
            
        except Exception as e:
            self.logger.error(f"Manual fault injection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Fault injection failed: {str(e)}",
                "fault_id": None
            }
    
    def inject_random_fault(self) -> Dict[str, Any]:
        """Inject a random fault for testing purposes."""
        # Select random fault type based on probabilities
        fault_type = self._select_random_fault_type()
        target = self._select_random_target(fault_type)
        
        return self.inject_manual_fault(
            fault_type=fault_type,
            target=target,
            description=f"Random {self.fault_types[fault_type]['name']}"
        )
    
    def start_auto_injection(self):
        """Start automatic fault injection."""
        if self.is_running:
            return {"success": False, "message": "Auto injection already running"}
        
        self.is_running = True
        self.auto_injection_thread = threading.Thread(target=self._auto_injection_loop)
        self.auto_injection_thread.daemon = True
        self.auto_injection_thread.start()
        
        self.logger.info(f"Started auto fault injection (interval: {self.auto_injection_interval}s)")
        return {"success": True, "message": "Auto fault injection started"}
    
    def stop_auto_injection(self):
        """Stop automatic fault injection."""
        self.is_running = False
        if self.auto_injection_thread:
            self.auto_injection_thread.join(timeout=5)
        
        self.logger.info("Stopped auto fault injection")
        return {"success": True, "message": "Auto fault injection stopped"}
    
    def _auto_injection_loop(self):
        """Main loop for automatic fault injection."""
        while self.is_running:
            try:
                time.sleep(self.auto_injection_interval)
                
                if not self.is_running:
                    break
                
                # Inject fault with configured probability
                if random.random() < self.auto_fault_probability:
                    fault_result = self.inject_random_fault()
                    if fault_result['success']:
                        self.logger.info(f"Auto-injected fault: {fault_result['fault_id']}")
                
            except Exception as e:
                self.logger.error(f"Auto injection loop error: {str(e)}")
                time.sleep(5)  # Wait before continuing
    
    def _select_random_fault_type(self) -> str:
        """Select random fault type based on configured probabilities."""
        fault_probs = {}
        for fault_type, config in self.config.get('fault_types', {}).items():
            fault_probs[fault_type] = config.get('probability', 0.2)
        
        # If no probabilities configured, use defaults
        if not fault_probs:
            fault_probs = {
                'node_down': 0.3,
                'link_down': 0.4,
                'congestion': 0.2,
                'packet_loss': 0.08,
                'cascading': 0.02
            }
        
        # Weighted random selection
        fault_types = list(fault_probs.keys())
        weights = list(fault_probs.values())
        
        return random.choices(fault_types, weights=weights)[0]
    
    def _select_random_target(self, fault_type: str) -> Any:
        """Select random target for fault type."""
        # Get a sample network to determine available targets
        sample_network = self.network_manager.get_network('rule_based')
        
        if fault_type == 'node_down':
            # Select random node
            nodes = list(sample_network.nodes())
            return random.choice(nodes) if nodes else 0
        
        elif fault_type == 'link_down':
            # Select random link
            edges = list(sample_network.edges())
            if edges:
                src, dst = random.choice(edges)
                return f"{src}-{dst}"
            return "0-1"
        
        elif fault_type == 'congestion':
            # Select random node for congestion
            nodes = list(sample_network.nodes())
            return random.choice(nodes) if nodes else 0
        
        elif fault_type == 'packet_loss':
            # Network-wide packet loss
            return "network_wide"
        
        elif fault_type == 'cascading':
            # Multiple targets for cascading failure
            return "multiple"
        
        return "unknown"
    
    def _estimate_recovery_time(self, fault_type: str) -> int:
        """Estimate recovery time for fault type."""
        time_range = self.fault_types.get(fault_type, {}).get('recovery_time_range', [10, 30])
        return random.randint(time_range[0], time_range[1])
    
    def get_fault_types(self) -> Dict[str, Dict[str, Any]]:
        """Get available fault types and their descriptions."""
        return self.fault_types.copy()
    
    def get_fault_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent fault injection history."""
        return self.fault_history[-limit:] if self.fault_history else []
    
    def get_active_faults(self) -> List[Dict[str, Any]]:
        """Get currently active/unresolved faults."""
        current_time = time.time()
        active_faults = []
        
        for fault in self.fault_history:
            fault_time = fault['timestamp']
            recovery_time = fault.get('expected_recovery_time', 30)
            
            # Consider fault active if within expected recovery window
            if current_time - fault_time < recovery_time:
                active_faults.append(fault)
        
        return active_faults
    
    def clear_fault_history(self):
        """Clear fault injection history."""
        self.fault_history.clear()
        self.logger.info("Fault history cleared")
    
    def add_injection_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback to be notified of fault injections."""
        self.injection_callbacks.append(callback)
    
    def remove_injection_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove fault injection callback."""
        if callback in self.injection_callbacks:
            self.injection_callbacks.remove(callback)
    
    def _notify_injection_callbacks(self, fault_record: Dict[str, Any]):
        """Notify all registered callbacks of fault injection."""
        for callback in self.injection_callbacks:
            try:
                callback(fault_record)
            except Exception as e:
                self.logger.error(f"Callback notification failed: {str(e)}")
    
    def inject_cascading_scenario(self) -> Dict[str, Any]:
        """Inject a complex cascading failure scenario."""
        try:
            scenario_id = f"cascade_{int(time.time())}"
            scenario_results = []
            
            # Step 1: Initial node failure
            initial_result = self.inject_manual_fault(
                'node_down',
                self._select_random_target('node_down'),
                f"Cascading scenario {scenario_id} - Initial failure"
            )
            scenario_results.append(initial_result)
            
            # Wait for initial impact
            time.sleep(2)
            
            # Step 2: Secondary link failure
            link_result = self.inject_manual_fault(
                'link_down',
                self._select_random_target('link_down'),
                f"Cascading scenario {scenario_id} - Secondary link failure"
            )
            scenario_results.append(link_result)
            
            # Wait for propagation
            time.sleep(3)
            
            # Step 3: Congestion due to rerouting
            congestion_result = self.inject_manual_fault(
                'congestion',
                self._select_random_target('congestion'),
                f"Cascading scenario {scenario_id} - Congestion from rerouting"
            )
            scenario_results.append(congestion_result)
            
            # Record scenario
            scenario_record = {
                'scenario_id': scenario_id,
                'timestamp': time.time(),
                'type': 'cascading_scenario',
                'steps': scenario_results,
                'total_faults': len(scenario_results),
                'description': 'Multi-step cascading failure scenario'
            }
            
            self.logger.info(f"Cascading scenario executed: {scenario_id}")
            
            return {
                "success": True,
                "message": f"Cascading scenario {scenario_id} executed",
                "scenario_record": scenario_record
            }
            
        except Exception as e:
            self.logger.error(f"Cascading scenario failed: {str(e)}")
            return {
                "success": False,
                "message": f"Cascading scenario failed: {str(e)}"
            }
    
    def inject_stress_test(self, duration: int = 60) -> Dict[str, Any]:
        """Inject multiple faults for stress testing."""
        try:
            test_id = f"stress_{int(time.time())}"
            test_results = []
            start_time = time.time()
            
            self.logger.info(f"Starting stress test {test_id} for {duration} seconds")
            
            while time.time() - start_time < duration:
                # Inject random fault
                fault_result = self.inject_random_fault()
                test_results.append(fault_result)
                
                # Wait random interval between 5-15 seconds
                wait_time = random.randint(5, 15)
                time.sleep(wait_time)
            
            stress_record = {
                'test_id': test_id,
                'start_time': start_time,
                'end_time': time.time(),
                'duration': duration,
                'total_faults': len(test_results),
                'successful_injections': sum(1 for r in test_results if r['success']),
                'fault_details': test_results
            }
            
            self.logger.info(f"Stress test completed: {test_id} "
                           f"({stress_record['successful_injections']}/{stress_record['total_faults']} successful)")
            
            return {
                "success": True,
                "message": f"Stress test {test_id} completed",
                "test_record": stress_record
            }
            
        except Exception as e:
            self.logger.error(f"Stress test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Stress test failed: {str(e)}"
            }
    
    def get_injection_stats(self) -> Dict[str, Any]:
        """Get fault injection statistics."""
        if not self.fault_history:
            return {
                "total_faults": 0,
                "faults_by_type": {},
                "success_rate": 0,
                "average_recovery_time": 0,
                "most_recent_fault": None
            }
        
        # Calculate statistics
        total_faults = len(self.fault_history)
        faults_by_type = {}
        successful_faults = 0
        total_recovery_time = 0
        
        for fault in self.fault_history:
            fault_type = fault['type']
            faults_by_type[fault_type] = faults_by_type.get(fault_type, 0) + 1
            
            # Count as successful if at least one agent was affected
            if any(fault.get('success_per_agent', {}).values()):
                successful_faults += 1
            
            total_recovery_time += fault.get('expected_recovery_time', 0)
        
        return {
            "total_faults": total_faults,
            "faults_by_type": faults_by_type,
            "success_rate": successful_faults / total_faults if total_faults > 0 else 0,
            "average_recovery_time": total_recovery_time / total_faults if total_faults > 0 else 0,
            "most_recent_fault": self.fault_history[-1] if self.fault_history else None,
            "auto_injection_running": self.is_running
        }