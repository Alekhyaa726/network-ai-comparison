"""
Simulation Engine for coordinated triple network simulation.
Manages the execution of three AI agents simultaneously on identical network scenarios.
"""
import time
import threading
import asyncio
from typing import Dict, List, Any, Optional, Callable
import logging
from enum import Enum

from ..models import RuleBasedAgent, RegressionAgent, RLAgent
from .network_manager import NetworkManager
from .fault_injector import FaultInjector
from .performance_monitor import PerformanceMonitor

class SimulationState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"

class SimulationEngine:
    """Coordinates the triple network AI comparison simulation."""
    
    def __init__(self, config_path: str = "/app/data/network_configs.json"):
        self.logger = logging.getLogger("simulation_engine")
        self.config_path = config_path
        
        # Core components
        self.network_manager = NetworkManager()
        self.fault_injector = FaultInjector(self.network_manager, config_path)
        self.performance_monitor = PerformanceMonitor(config_path)
        
        # AI Agents
        self.agents = {
            'rule_based': RuleBasedAgent(),
            'regression': RegressionAgent(),
            'rl': RLAgent()
        }
        
        # Simulation state
        self.state = SimulationState.STOPPED
        self.simulation_thread = None
        self.update_interval = 1.0  # seconds
        self.max_simulation_time = 3600  # seconds
        self.simulation_start_time = None
        self.simulation_id = None
        
        # Event handling
        self.event_callbacks = []
        self.state_change_callbacks = []
        
        # Simulation statistics
        self.simulation_stats = {
            'total_faults_injected': 0,
            'total_decisions_made': 0,
            'total_healing_actions': 0,
            'agents_active': 0,
            'current_fault_count': 0
        }
        
        # Synchronization
        self.simulation_lock = threading.Lock()
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all simulation components."""
        try:
            # Activate all agents
            for agent in self.agents.values():
                agent.activate()
            
            # Set up fault injection callback
            self.fault_injector.add_injection_callback(self._on_fault_injected)
            
            self.logger.info("Simulation engine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize simulation engine: {str(e)}")
            self.state = SimulationState.ERROR
    
    def start_simulation(self, simulation_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start the triple network simulation.
        
        Args:
            simulation_config: Optional configuration override
            
        Returns:
            Simulation start result
        """
        with self.simulation_lock:
            if self.state != SimulationState.STOPPED:
                return {
                    "success": False,
                    "message": f"Cannot start simulation. Current state: {self.state.value}",
                    "simulation_id": None
                }
            
            try:
                self.state = SimulationState.STARTING
                self._notify_state_change()
                
                # Apply configuration
                if simulation_config:
                    self._apply_simulation_config(simulation_config)
                
                # Reset all components
                self._reset_simulation_components()
                
                # Generate simulation ID
                self.simulation_id = f"sim_{int(time.time())}"
                self.simulation_start_time = time.time()
                
                # Start monitoring
                self.performance_monitor.start_monitoring()
                
                # Start main simulation thread
                self.simulation_thread = threading.Thread(target=self._simulation_loop)
                self.simulation_thread.daemon = True
                self.simulation_thread.start()
                
                self.state = SimulationState.RUNNING
                self._notify_state_change()
                
                self.logger.info(f"Simulation started: {self.simulation_id}")
                
                return {
                    "success": True,
                    "message": "Simulation started successfully",
                    "simulation_id": self.simulation_id,
                    "start_time": self.simulation_start_time
                }
                
            except Exception as e:
                self.state = SimulationState.ERROR
                self._notify_state_change()
                self.logger.error(f"Failed to start simulation: {str(e)}")
                
                return {
                    "success": False,
                    "message": f"Failed to start simulation: {str(e)}",
                    "simulation_id": None
                }
    
    def stop_simulation(self) -> Dict[str, Any]:
        """Stop the current simulation."""
        with self.simulation_lock:
            if self.state == SimulationState.STOPPED:
                return {
                    "success": False,
                    "message": "No simulation is currently running",
                    "simulation_id": self.simulation_id
                }
            
            try:
                self.state = SimulationState.STOPPING
                self._notify_state_change()
                
                # Stop auto fault injection
                self.fault_injector.stop_auto_injection()
                
                # Wait for simulation thread to finish
                if self.simulation_thread and self.simulation_thread.is_alive():
                    self.simulation_thread.join(timeout=10)
                
                # Stop monitoring
                self.performance_monitor.stop_monitoring()
                
                # End RL episode
                self.agents['rl'].end_episode()
                
                # Calculate simulation duration
                duration = time.time() - self.simulation_start_time if self.simulation_start_time else 0
                
                self.state = SimulationState.STOPPED
                self._notify_state_change()
                
                self.logger.info(f"Simulation stopped: {self.simulation_id} (duration: {duration:.1f}s)")
                
                return {
                    "success": True,
                    "message": "Simulation stopped successfully",
                    "simulation_id": self.simulation_id,
                    "duration": duration,
                    "final_stats": self.simulation_stats.copy()
                }
                
            except Exception as e:
                self.state = SimulationState.ERROR
                self._notify_state_change()
                self.logger.error(f"Failed to stop simulation: {str(e)}")
                
                return {
                    "success": False,
                    "message": f"Failed to stop simulation: {str(e)}",
                    "simulation_id": self.simulation_id
                }
    
    def pause_simulation(self) -> Dict[str, Any]:
        """Pause the current simulation."""
        if self.state != SimulationState.RUNNING:
            return {
                "success": False,
                "message": f"Cannot pause. Current state: {self.state.value}"
            }
        
        self.state = SimulationState.PAUSED
        self._notify_state_change()
        
        self.logger.info(f"Simulation paused: {self.simulation_id}")
        return {"success": True, "message": "Simulation paused"}
    
    def resume_simulation(self) -> Dict[str, Any]:
        """Resume a paused simulation."""
        if self.state != SimulationState.PAUSED:
            return {
                "success": False,
                "message": f"Cannot resume. Current state: {self.state.value}"
            }
        
        self.state = SimulationState.RUNNING
        self._notify_state_change()
        
        self.logger.info(f"Simulation resumed: {self.simulation_id}")
        return {"success": True, "message": "Simulation resumed"}
    
    def inject_fault_manually(self, fault_type: str, target: Any = None, description: str = "") -> Dict[str, Any]:
        """Manually inject a fault during simulation."""
        if self.state not in [SimulationState.RUNNING, SimulationState.PAUSED]:
            return {
                "success": False,
                "message": "Cannot inject fault. Simulation not running."
            }
        
        # Inject fault through fault injector
        result = self.fault_injector.inject_manual_fault(fault_type, target, description)
        
        if result['success']:
            self.simulation_stats['total_faults_injected'] += 1
            self.simulation_stats['current_fault_count'] += 1
            
            # Trigger agent responses
            asyncio.create_task(self._process_fault_response(result['fault_record']))
        
        return result
    
    def _simulation_loop(self):
        """Main simulation loop."""
        self.logger.info(f"Starting simulation loop for {self.simulation_id}")
        
        try:
            while self.state in [SimulationState.RUNNING, SimulationState.PAUSED]:
                # Check if simulation should continue
                if self._should_stop_simulation():
                    break
                
                # Skip processing if paused
                if self.state == SimulationState.PAUSED:
                    time.sleep(1)
                    continue
                
                # Process one simulation step
                self._simulation_step()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except Exception as e:
            self.logger.error(f"Simulation loop error: {str(e)}")
            self.state = SimulationState.ERROR
            self._notify_state_change()
        
        self.logger.info(f"Simulation loop ended for {self.simulation_id}")
    
    def _simulation_step(self):
        """Execute one simulation step."""
        try:
            # Update network states for all agents
            for agent_id in self.agents.keys():
                network_state = self.network_manager.get_network_state(agent_id)
                if network_state:
                    # Record network state
                    self.performance_monitor.record_network_state(agent_id, network_state)
                    
                    # Let agent process the current state
                    network = self.network_manager.get_network(agent_id)
                    if network:
                        agent = self.agents[agent_id]
                        
                        # Process network event (will detect faults and take actions)
                        decision_result = agent.process_network_event(network_state, network)
                        
                        # Record agent decision
                        self.performance_monitor.record_agent_decision(agent_id, decision_result)
                        
                        # Apply healing result to network
                        if decision_result.get('result', {}).get('success', False):
                            self.network_manager.heal_network(agent_id, decision_result['result'])
                        
                        # Update statistics
                        self.simulation_stats['total_decisions_made'] += 1
                        if decision_result.get('action') != 'maintain':
                            self.simulation_stats['total_healing_actions'] += 1
            
            # Update active agent count
            self.simulation_stats['agents_active'] = sum(1 for agent in self.agents.values() if agent.is_active)
            
            # Notify event callbacks
            self._notify_event_callbacks({
                'type': 'simulation_step',
                'timestamp': time.time(),
                'stats': self.simulation_stats.copy()
            })
            
        except Exception as e:
            self.logger.error(f"Simulation step error: {str(e)}")
    
    async def _process_fault_response(self, fault_record: Dict[str, Any]):
        """Process agent responses to injected fault."""
        try:
            fault_type = fault_record['type']
            fault_target = fault_record['target']
            
            # Give agents time to detect and respond
            await asyncio.sleep(2)
            
            # Collect recovery results from all agents
            recovery_results = {}
            
            for agent_id in self.agents.keys():
                # Get current network state after fault
                network_state = self.network_manager.get_network_state(agent_id)
                network = self.network_manager.get_network(agent_id)
                
                if network_state and network:
                    # Let agent respond to the fault
                    agent = self.agents[agent_id]
                    response = agent.process_network_event(network_state, network)
                    recovery_results[agent_id] = response.get('result', {})
                    
                    # Apply healing
                    if response.get('result', {}).get('success', False):
                        self.network_manager.heal_network(agent_id, response['result'])
            
            # Record fault recovery performance
            self.performance_monitor.record_fault_recovery(fault_record, recovery_results)
            
            # Update fault count
            self.simulation_stats['current_fault_count'] = max(0, self.simulation_stats['current_fault_count'] - 1)
            
            # Notify event callbacks
            self._notify_event_callbacks({
                'type': 'fault_response',
                'timestamp': time.time(),
                'fault_record': fault_record,
                'recovery_results': recovery_results
            })
            
        except Exception as e:
            self.logger.error(f"Fault response processing error: {str(e)}")
    
    def _should_stop_simulation(self) -> bool:
        """Check if simulation should stop."""
        if self.state == SimulationState.STOPPING:
            return True
        
        # Check time limit
        if self.simulation_start_time:
            elapsed = time.time() - self.simulation_start_time
            if elapsed >= self.max_simulation_time:
                self.logger.info(f"Simulation time limit reached: {elapsed:.1f}s")
                return True
        
        return False
    
    def _reset_simulation_components(self):
        """Reset all simulation components for new simulation."""
        # Reset network states
        self.network_manager.reset_all_networks()
        
        # Reset agent metrics
        for agent in self.agents.values():
            agent.reset_metrics()
        
        # Reset performance monitor
        self.performance_monitor.reset_metrics()
        
        # Reset fault injector
        self.fault_injector.clear_fault_history()
        
        # Reset statistics
        self.simulation_stats = {
            'total_faults_injected': 0,
            'total_decisions_made': 0,
            'total_healing_actions': 0,
            'agents_active': len(self.agents),
            'current_fault_count': 0
        }
    
    def _apply_simulation_config(self, config: Dict[str, Any]):
        """Apply simulation configuration."""
        if 'update_interval' in config:
            self.update_interval = config['update_interval']
        
        if 'max_simulation_time' in config:
            self.max_simulation_time = config['max_simulation_time']
        
        if 'auto_fault_injection' in config:
            if config['auto_fault_injection']:
                self.fault_injector.start_auto_injection()
    
    def _on_fault_injected(self, fault_record: Dict[str, Any]):
        """Callback for when a fault is injected."""
        self.simulation_stats['total_faults_injected'] += 1
        self.simulation_stats['current_fault_count'] += 1
        
        # Create async task to process fault response
        if self.state == SimulationState.RUNNING:
            asyncio.create_task(self._process_fault_response(fault_record))
    
    def get_simulation_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        status = {
            'simulation_id': self.simulation_id,
            'state': self.state.value,
            'start_time': self.simulation_start_time,
            'elapsed_time': 0,
            'remaining_time': 0,
            'stats': self.simulation_stats.copy(),
            'agents_status': {},
            'network_status': {},
            'fault_injection_status': {},
            'monitoring_status': {}
        }
        
        # Calculate times
        if self.simulation_start_time:
            status['elapsed_time'] = time.time() - self.simulation_start_time
            status['remaining_time'] = max(0, self.max_simulation_time - status['elapsed_time'])
        
        # Agent status
        for agent_id, agent in self.agents.items():
            agent_metrics = agent.get_performance_metrics()
            status['agents_status'][agent_id] = {
                'is_active': agent.is_active,
                'decision_count': agent_metrics.get('decision_count', 0),
                'success_rate': agent_metrics.get('success_rate', 0),
                'last_decision_time': agent.last_decision_time
            }
            
            # Add agent-specific metrics
            if agent_id == 'rl':
                rl_metrics = agent.get_rl_metrics()
                status['agents_status'][agent_id].update(rl_metrics)
            elif agent_id == 'regression':
                model_info = agent.get_model_info()
                status['agents_status'][agent_id].update(model_info)
        
        # Network status
        status['network_status'] = self.network_manager.get_network_stats()
        
        # Fault injection status
        status['fault_injection_status'] = self.fault_injector.get_injection_stats()
        
        # Monitoring status
        status['monitoring_status'] = self.performance_monitor.get_monitoring_status()
        
        return status
    
    def get_real_time_kpis(self) -> Dict[str, Any]:
        """Get real-time KPIs for dashboard."""
        return self.performance_monitor.get_real_time_kpis()
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return self.performance_monitor.generate_comparison_report()
    
    def add_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for simulation events."""
        self.event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Remove simulation event callback."""
        if callback in self.event_callbacks:
            self.event_callbacks.remove(callback)
    
    def add_state_change_callback(self, callback: Callable[[SimulationState], None]):
        """Add callback for state changes."""
        self.state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable[[SimulationState], None]):
        """Remove state change callback."""
        if callback in self.state_change_callbacks:
            self.state_change_callbacks.remove(callback)
    
    def _notify_event_callbacks(self, event_data: Dict[str, Any]):
        """Notify all event callbacks."""
        for callback in self.event_callbacks:
            try:
                callback(event_data)
            except Exception as e:
                self.logger.error(f"Event callback error: {str(e)}")
    
    def _notify_state_change(self):
        """Notify all state change callbacks."""
        for callback in self.state_change_callbacks:
            try:
                callback(self.state)
            except Exception as e:
                self.logger.error(f"State change callback error: {str(e)}")
    
    def get_agent_logs(self, agent_id: str, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent decision logs for specific agent."""
        if agent_id in self.agents:
            return self.agents[agent_id].get_recent_decisions(count)
        return []
    
    def export_simulation_data(self) -> Dict[str, Any]:
        """Export all simulation data for analysis."""
        return {
            'simulation_info': {
                'simulation_id': self.simulation_id,
                'start_time': self.simulation_start_time,
                'state': self.state.value,
                'stats': self.simulation_stats
            },
            'performance_metrics': self.performance_monitor.export_metrics('json'),
            'fault_history': self.fault_injector.get_fault_history(),
            'agent_decisions': {
                agent_id: agent.get_recent_decisions(100)
                for agent_id, agent in self.agents.items()
            },
            'network_states': self.network_manager.get_network_stats(),
            'comparison_report': self.generate_performance_report()
        }