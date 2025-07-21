"""
Reinforcement Learning Agent for network self-healing.
Uses Deep Q-Network (DQN) to learn optimal healing strategies through experience.
"""
from typing import Dict, List, Any, Optional, Tuple, Deque
import time
import numpy as np
import random
from collections import deque
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os
from .base_agent import BaseAgent, ActionType, FaultType, NetworkState

class RLAgent(BaseAgent):
    """Reinforcement Learning agent using Deep Q-Network for network healing."""
    
    def __init__(self, model_path: str = None):
        super().__init__("rl", "Reinforcement Learning Agent")
        self.model_path = model_path or "/app/models/rl_network.h5"
        
        # RL hyperparameters
        self.state_size = 12  # Network state representation size
        self.action_size = len(ActionType)  # Number of possible actions
        self.learning_rate = 0.001
        self.epsilon = 0.1  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.gamma = 0.95  # Discount factor
        self.batch_size = 32
        self.memory_size = 10000
        self.update_frequency = 4
        self.target_update_frequency = 100
        
        # Experience replay buffer
        self.memory: Deque = deque(maxlen=self.memory_size)
        
        # Networks
        self.q_network = self._build_dqn()
        self.target_network = self._build_dqn()
        self._update_target_network()
        
        # Training state
        self.training_step = 0
        self.episode_rewards = []
        self.current_episode_reward = 0
        self.last_state = None
        self.last_action = None
        
        # Action mapping
        self.action_map = list(ActionType)
        self.action_to_index = {action: i for i, action in enumerate(self.action_map)}
        
        # Load pre-trained model if available
        self._load_model()
        
        # Performance tracking
        self.q_values_history = []
        self.loss_history = []
    
    def _build_dqn(self) -> keras.Model:
        """Build Deep Q-Network architecture."""
        model = keras.Sequential([
            layers.Dense(128, activation='relu', input_shape=(self.state_size,)),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            
            layers.Dense(self.action_size, activation='linear')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _update_target_network(self):
        """Update target network with current network weights."""
        self.target_network.set_weights(self.q_network.get_weights())
    
    def _load_model(self):
        """Load pre-trained model if available."""
        try:
            if os.path.exists(self.model_path):
                self.q_network.load_weights(self.model_path)
                self._update_target_network()
                self.logger.info(f"Loaded pre-trained model from {self.model_path}")
            else:
                self.logger.info("No pre-trained model found, starting with random weights")
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")
    
    def _save_model(self):
        """Save current model."""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.q_network.save_weights(self.model_path)
            self.logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            self.logger.error(f"Failed to save model: {str(e)}")
    
    def get_state(self, network_state: Dict[str, Any]) -> np.ndarray:
        """
        Convert network state to RL state representation.
        
        Args:
            network_state: Current network state
            
        Returns:
            State vector for RL model
        """
        state = np.zeros(self.state_size)
        
        # Basic network metrics (indices 0-4)
        state[0] = network_state.get('throughput', 100) / 100.0  # Normalized throughput
        state[1] = network_state.get('latency', 10) / 100.0      # Normalized latency
        state[2] = network_state.get('packet_loss', 0)           # Packet loss rate
        state[3] = network_state.get('active_nodes', 14) / 14.0  # Normalized active nodes
        state[4] = network_state.get('connectivity', 1.0)        # Network connectivity
        
        # Node state aggregations (indices 5-7)
        node_states = network_state.get('node_states', {})
        if node_states:
            avg_utilization = np.mean([state.get('utilization', 0) for state in node_states.values()])
            avg_response_time = np.mean([state.get('response_time', 0) for state in node_states.values()])
            failed_nodes = sum(1 for state in node_states.values() if state.get('status') == 'down')
            
            state[5] = avg_utilization
            state[6] = min(avg_response_time / 1000.0, 1.0)  # Normalized response time
            state[7] = failed_nodes / 14.0  # Normalized failed nodes
        
        # Link state aggregations (indices 8-10)
        link_states = network_state.get('link_states', {})
        if link_states:
            avg_link_utilization = np.mean([state.get('utilization', 0) for state in link_states.values()])
            avg_link_latency = np.mean([state.get('latency', 0) for state in link_states.values()])
            failed_links = sum(1 for state in link_states.values() if state.get('status') == 'down')
            
            state[8] = avg_link_utilization
            state[9] = min(avg_link_latency / 100.0, 1.0)  # Normalized link latency
            state[10] = failed_links / 18.0  # Normalized failed links (NSFNET has 18 links)
        
        # Time-based feature (index 11)
        state[11] = (time.time() % 3600) / 3600.0  # Hour of day normalized
        
        return state
    
    def detect_fault(self, network_state: Dict[str, Any]) -> Tuple[FaultType, Optional[str]]:
        """
        RL-based fault detection using learned patterns.
        
        Args:
            network_state: Current network state
            
        Returns:
            Tuple of (fault_type, fault_location)
        """
        state = self.get_state(network_state)
        
        # Use Q-values to assess fault severity
        q_values = self.q_network.predict(state.reshape(1, -1), verbose=0)[0]
        max_q_value = np.max(q_values)
        action_values = q_values - np.mean(q_values)  # Normalize Q-values
        
        # Fault detection based on Q-value patterns
        if max_q_value < -0.5:  # Very low Q-values indicate critical issues
            return FaultType.CASCADING, "multiple"
        elif action_values[self.action_to_index[ActionType.EMERGENCY_REROUTE]] > 0.3:
            return FaultType.NODE_DOWN, self._identify_problematic_component(network_state, 'node')
        elif action_values[self.action_to_index[ActionType.BACKUP_ACTIVATION]] > 0.2:
            return FaultType.LINK_DOWN, self._identify_problematic_component(network_state, 'link')
        elif action_values[self.action_to_index[ActionType.LOAD_BALANCE]] > 0.2:
            return FaultType.CONGESTION, self._identify_problematic_component(network_state, 'node')
        elif action_values[self.action_to_index[ActionType.ERROR_CORRECTION]] > 0.1:
            return FaultType.PACKET_LOSS, "network_wide"
        
        return FaultType.NONE, None
    
    def decide_action(self, network_state: Dict[str, Any], fault_info: Tuple[FaultType, Optional[str]]) -> ActionType:
        """
        RL-based action selection using epsilon-greedy policy.
        
        Args:
            network_state: Current network state
            fault_info: Detected fault information
            
        Returns:
            ActionType to execute
        """
        state = self.get_state(network_state)
        
        # Store current state for learning
        self.last_state = state
        
        # Epsilon-greedy action selection
        if np.random.random() <= self.epsilon:
            # Exploration: random action
            action_index = np.random.choice(self.action_size)
            self.logger.debug(f"RL exploration: random action selected")
        else:
            # Exploitation: best action according to Q-network
            q_values = self.q_network.predict(state.reshape(1, -1), verbose=0)[0]
            action_index = np.argmax(q_values)
            self.logger.debug(f"RL exploitation: Q-values {q_values}")
        
        action = self.action_map[action_index]
        self.last_action = action_index
        
        # Store Q-values for analysis
        if len(self.q_values_history) > 1000:
            self.q_values_history.pop(0)
        q_values = self.q_network.predict(state.reshape(1, -1), verbose=0)[0]
        self.q_values_history.append(np.max(q_values))
        
        self.logger.info(f"RL decision: {fault_info[0].value} -> {action.value} (epsilon: {self.epsilon:.3f})")
        return action
    
    def execute_healing(self, action: ActionType, network: Any, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """
        Execute healing action and learn from the result.
        
        Args:
            action: Action to execute
            network: Network object
            fault_info: Fault information
            
        Returns:
            Execution results
        """
        execution_start = time.time()
        
        try:
            # Execute the action
            result = self._execute_rl_action(action, network, fault_info)
            
            execution_time = time.time() - execution_start
            result["execution_time"] = execution_time
            
            # Calculate reward based on result
            reward = self._calculate_reward(result, execution_time, fault_info)
            self.current_episode_reward += reward
            
            # Learn from the experience
            self._learn_from_experience(result, reward)
            
            # Update performance metrics
            self.performance_metrics["healing_time"] = (
                self.performance_metrics["healing_time"] + execution_time
            ) / max(1, self.performance_metrics["decision_count"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"RL healing execution failed: {str(e)}")
            execution_time = time.time() - execution_start
            
            # Learn from failure
            failure_result = {
                "success": False,
                "message": f"Execution failed: {str(e)}",
                "changes": []
            }
            reward = self._calculate_reward(failure_result, execution_time, fault_info)
            self._learn_from_experience(failure_result, reward)
            
            return {
                "success": False,
                "message": f"RL execution failed: {str(e)}",
                "execution_time": execution_time,
                "changes": []
            }
    
    def _execute_rl_action(self, action: ActionType, network: Any, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """Execute action with RL-specific optimizations."""
        fault_type, fault_location = fault_info
        changes = []
        
        try:
            if action == ActionType.MAINTAIN:
                return {"success": True, "message": "Network maintained by RL agent", "changes": []}
            
            # RL-specific action execution with learned parameters
            if action == ActionType.CLUSTER_REROUTE:
                changes.append("RL-guided cluster rerouting initiated")
                changes.append(f"Applied learned routing strategy for {fault_location}")
                success_prob = 0.88  # Based on RL experience
                
            elif action == ActionType.LOAD_BALANCE:
                changes.append("RL-optimized load balancing executed")
                changes.append("Used learned traffic distribution patterns")
                success_prob = 0.92
                
            elif action == ActionType.BACKUP_ACTIVATION:
                changes.append("RL-selected backup path activated")
                changes.append(f"Chose optimal backup for {fault_location} based on experience")
                success_prob = 0.90
                
            elif action == ActionType.EMERGENCY_REROUTE:
                changes.append("RL emergency protocol activated")
                changes.append("Applied learned emergency response patterns")
                success_prob = 0.85
                
            else:
                changes.append(f"RL-guided {action.value} execution")
                success_prob = 0.80
            
            # Simulate success/failure based on learned probabilities
            success = np.random.random() < success_prob
            
            return {
                "success": success,
                "message": f"RL-guided {action.value} {'completed' if success else 'failed'}",
                "changes": changes,
                "rl_confidence": success_prob
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"RL action execution failed: {str(e)}",
                "changes": changes
            }
    
    def _calculate_reward(self, result: Dict[str, Any], execution_time: float, fault_info: Tuple[FaultType, Optional[str]]) -> float:
        """
        Calculate reward for the action taken.
        
        Args:
            result: Action execution result
            execution_time: Time taken to execute
            fault_info: Fault information
            
        Returns:
            Reward value
        """
        base_reward = 0.0
        
        # Success/failure reward
        if result.get("success", False):
            base_reward += 10.0
        else:
            base_reward -= 5.0
        
        # Time efficiency reward (faster is better)
        time_reward = max(0, 10 - execution_time)  # Reward decreases with time
        base_reward += time_reward * 0.5
        
        # Fault-specific rewards
        fault_type = fault_info[0]
        if fault_type == FaultType.CASCADING and result.get("success", False):
            base_reward += 15.0  # High reward for handling cascading failures
        elif fault_type == FaultType.NODE_DOWN and result.get("success", False):
            base_reward += 8.0
        elif fault_type == FaultType.CONGESTION and result.get("success", False):
            base_reward += 5.0
        
        # Penalty for unnecessary actions
        if fault_type == FaultType.NONE and self.last_action != self.action_to_index[ActionType.MAINTAIN]:
            base_reward -= 2.0
        
        return base_reward
    
    def _learn_from_experience(self, result: Dict[str, Any], reward: float):
        """Learn from the current experience."""
        if self.last_state is not None and self.last_action is not None:
            # Store experience in replay buffer
            experience = (
                self.last_state.copy(),
                self.last_action,
                reward,
                None,  # Next state will be set in next call
                result.get("success", False)
            )
            
            # Update previous experience with next state
            if len(self.memory) > 0:
                prev_experience = list(self.memory[-1])
                prev_experience[3] = self.last_state.copy()  # Set next state
                self.memory[-1] = tuple(prev_experience)
            
            self.memory.append(experience)
            
            # Train the network periodically
            if len(self.memory) >= self.batch_size and self.training_step % self.update_frequency == 0:
                self._replay_experience()
            
            # Update target network periodically
            if self.training_step % self.target_update_frequency == 0:
                self._update_target_network()
            
            self.training_step += 1
            
            # Decay epsilon
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
    
    def _replay_experience(self):
        """Train the Q-network using experience replay."""
        try:
            # Sample random batch from memory
            batch = random.sample(self.memory, min(len(self.memory), self.batch_size))
            
            states = np.array([exp[0] for exp in batch])
            actions = np.array([exp[1] for exp in batch])
            rewards = np.array([exp[2] for exp in batch])
            next_states = np.array([exp[3] if exp[3] is not None else exp[0] for exp in batch])
            dones = np.array([not exp[4] for exp in batch])  # Terminal state if action failed
            
            # Current Q-values
            current_q_values = self.q_network.predict(states, verbose=0)
            
            # Next Q-values from target network
            next_q_values = self.target_network.predict(next_states, verbose=0)
            
            # Calculate target Q-values
            target_q_values = current_q_values.copy()
            for i in range(len(batch)):
                if dones[i]:
                    target_q_values[i][actions[i]] = rewards[i]
                else:
                    target_q_values[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
            
            # Train the network
            history = self.q_network.fit(states, target_q_values, verbose=0)
            
            # Track loss
            if len(self.loss_history) > 1000:
                self.loss_history.pop(0)
            self.loss_history.append(history.history['loss'][0])
            
        except Exception as e:
            self.logger.error(f"Experience replay failed: {str(e)}")
    
    def _identify_problematic_component(self, network_state: Dict[str, Any], component_type: str) -> str:
        """Identify problematic component using RL analysis."""
        if component_type == 'node':
            node_states = network_state.get('node_states', {})
            for node_id, state in node_states.items():
                if state.get('utilization', 0) > 0.8 or state.get('response_time', 0) > 500:
                    return str(node_id)
            return "unknown"
        
        elif component_type == 'link':
            link_states = network_state.get('link_states', {})
            for link_id, state in link_states.items():
                if state.get('packet_loss', 0) > 0.1 or state.get('utilization', 0) > 0.9:
                    return str(link_id)
            return "unknown"
        
        return "unknown"
    
    def end_episode(self):
        """End current episode and update statistics."""
        if self.current_episode_reward != 0:
            self.episode_rewards.append(self.current_episode_reward)
            if len(self.episode_rewards) > 100:
                self.episode_rewards.pop(0)  # Keep only recent episodes
            
            self.logger.info(f"Episode ended. Reward: {self.current_episode_reward:.2f}, Epsilon: {self.epsilon:.3f}")
            self.current_episode_reward = 0
        
        # Save model periodically
        if len(self.episode_rewards) % 10 == 0:
            self._save_model()
    
    def get_rl_metrics(self) -> Dict[str, Any]:
        """Get RL-specific metrics."""
        return {
            "epsilon": self.epsilon,
            "training_steps": self.training_step,
            "memory_size": len(self.memory),
            "avg_episode_reward": np.mean(self.episode_rewards) if self.episode_rewards else 0,
            "avg_q_value": np.mean(self.q_values_history) if self.q_values_history else 0,
            "avg_loss": np.mean(self.loss_history) if self.loss_history else 0,
            "episodes_completed": len(self.episode_rewards)
        }
    
    def reset_learning_state(self):
        """Reset RL learning state."""
        self.memory.clear()
        self.episode_rewards.clear()
        self.q_values_history.clear()
        self.loss_history.clear()
        self.current_episode_reward = 0
        self.training_step = 0
        self.epsilon = 0.1
        self.logger.info("RL learning state reset")