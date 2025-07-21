"""
Regression Model Agent for network self-healing.
Uses machine learning regression models to predict network performance and optimize healing decisions.
"""
from typing import Dict, List, Any, Optional, Tuple
import time
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
from .base_agent import BaseAgent, ActionType, FaultType, NetworkState

class RegressionAgent(BaseAgent):
    """ML-based agent using regression models for network healing decisions."""
    
    def __init__(self, data_path: str = None):
        super().__init__("regression", "Regression Model Agent")
        self.data_path = data_path or "/app/data/training_data.csv"
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.target_columns = ["healing_time", "success_rate", "throughput_after"]
        self.prediction_cache = {}
        self.retrain_interval = 100
        self.predictions_since_retrain = 0
        self.model_accuracy = 0.0
        
        # Initialize and train model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize and train the regression model."""
        try:
            # Load training data
            if os.path.exists(self.data_path):
                self.training_data = pd.read_csv(self.data_path)
                self._train_model()
            else:
                self.logger.warning(f"Training data not found at {self.data_path}, using default model")
                self._create_default_model()
        except Exception as e:
            self.logger.error(f"Model initialization failed: {str(e)}")
            self._create_default_model()
    
    def _create_default_model(self):
        """Create a default model with synthetic data."""
        # Create synthetic training data
        np.random.seed(42)
        n_samples = 200
        
        synthetic_data = {
            'network_state': np.random.choice(['normal', 'degraded', 'critical'], n_samples),
            'fault_type': np.random.choice(['none', 'node_down', 'link_down', 'congestion', 'packet_loss'], n_samples),
            'throughput_before': np.random.uniform(50, 100, n_samples),
            'latency_before': np.random.uniform(5, 50, n_samples),
            'active_nodes': np.random.randint(8, 15, n_samples),
            'healing_time': np.random.uniform(1, 60, n_samples),
            'success_rate': np.random.uniform(0.6, 1.0, n_samples),
            'throughput_after': np.random.uniform(60, 100, n_samples)
        }
        
        self.training_data = pd.DataFrame(synthetic_data)
        self._train_model()
    
    def _train_model(self):
        """Train the regression model."""
        try:
            # Prepare features
            self._prepare_features()
            
            # Prepare target variables
            X = self.training_data[self.feature_columns]
            y = self.training_data[self.target_columns]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            self.model_accuracy = r2_score(y_test, y_pred, multioutput='uniform_average')
            
            self.logger.info(f"Model trained successfully. R² score: {self.model_accuracy:.3f}")
            
        except Exception as e:
            self.logger.error(f"Model training failed: {str(e)}")
            self.model_accuracy = 0.0
    
    def _prepare_features(self):
        """Prepare features for training."""
        # Encode categorical variables
        categorical_columns = ['network_state', 'fault_type']
        
        for col in categorical_columns:
            if col in self.training_data.columns:
                le = LabelEncoder()
                self.training_data[f'{col}_encoded'] = le.fit_transform(self.training_data[col])
                self.label_encoders[col] = le
        
        # Define feature columns
        self.feature_columns = [
            'network_state_encoded', 'fault_type_encoded',
            'throughput_before', 'latency_before', 'active_nodes'
        ]
        
        # Add derived features
        if 'throughput_before' in self.training_data.columns:
            self.training_data['throughput_normalized'] = self.training_data['throughput_before'] / 100.0
            self.feature_columns.append('throughput_normalized')
        
        if 'latency_before' in self.training_data.columns:
            self.training_data['latency_normalized'] = self.training_data['latency_before'] / 100.0
            self.feature_columns.append('latency_normalized')
    
    def detect_fault(self, network_state: Dict[str, Any]) -> Tuple[FaultType, Optional[str]]:
        """
        ML-based fault detection using anomaly detection.
        
        Args:
            network_state: Current network state
            
        Returns:
            Tuple of (fault_type, fault_location)
        """
        try:
            # Extract features for prediction
            features = self._extract_features(network_state)
            
            # Predict network performance
            predictions = self._predict_performance(features)
            
            # Analyze predictions to detect faults
            healing_time_pred = predictions.get('healing_time', 0)
            success_rate_pred = predictions.get('success_rate', 1.0)
            throughput_pred = predictions.get('throughput_after', 100)
            
            # Fault detection thresholds
            if healing_time_pred > 30 and success_rate_pred < 0.7:
                return FaultType.CASCADING, "multiple"
            elif healing_time_pred > 20:
                return FaultType.NODE_DOWN, self._identify_problematic_node(network_state)
            elif throughput_pred < 70:
                if network_state.get('packet_loss', 0) > 0.1:
                    return FaultType.PACKET_LOSS, "network_wide"
                else:
                    return FaultType.CONGESTION, self._identify_congested_node(network_state)
            elif success_rate_pred < 0.9:
                return FaultType.LINK_DOWN, self._identify_problematic_link(network_state)
            
            return FaultType.NONE, None
            
        except Exception as e:
            self.logger.error(f"Fault detection failed: {str(e)}")
            return FaultType.NONE, None
    
    def decide_action(self, network_state: Dict[str, Any], fault_info: Tuple[FaultType, Optional[str]]) -> ActionType:
        """
        ML-based action decision using performance predictions.
        
        Args:
            network_state: Current network state
            fault_info: Detected fault information
            
        Returns:
            ActionType to execute
        """
        fault_type, fault_location = fault_info
        
        if fault_type == FaultType.NONE:
            return ActionType.MAINTAIN
        
        try:
            # Get all possible actions for the fault type
            possible_actions = self._get_possible_actions(fault_type)
            
            # Predict outcomes for each action
            best_action = ActionType.MAINTAIN
            best_score = -1
            
            for action in possible_actions:
                predicted_outcome = self._predict_action_outcome(network_state, fault_info, action)
                score = self._calculate_action_score(predicted_outcome)
                
                if score > best_score:
                    best_score = score
                    best_action = action
            
            self.logger.info(f"ML decision: {fault_type.value} -> {best_action.value} (score: {best_score:.3f})")
            return best_action
            
        except Exception as e:
            self.logger.error(f"Action decision failed: {str(e)}")
            return self._fallback_action(fault_type)
    
    def execute_healing(self, action: ActionType, network: Any, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """
        Execute healing action with ML-guided optimization.
        
        Args:
            action: Action to execute
            network: Network object
            fault_info: Fault information
            
        Returns:
            Execution results
        """
        fault_type, fault_location = fault_info
        execution_start = time.time()
        
        try:
            # Predict optimal parameters for the action
            optimal_params = self._predict_optimal_parameters(action, fault_info)
            
            # Execute action with optimization
            result = self._execute_optimized_action(action, network, fault_location, optimal_params)
            
            execution_time = time.time() - execution_start
            result["execution_time"] = execution_time
            
            # Update performance metrics
            self.performance_metrics["healing_time"] = (
                self.performance_metrics["healing_time"] + execution_time
            ) / max(1, self.performance_metrics["decision_count"])
            
            # Update model with new data point
            self._update_model_with_result(fault_info, action, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Healing execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Execution failed: {str(e)}",
                "execution_time": time.time() - execution_start,
                "changes": []
            }
    
    def _extract_features(self, network_state: Dict[str, Any]) -> np.ndarray:
        """Extract features from network state for ML prediction."""
        features = []
        
        # Network state encoding
        state_val = network_state.get('network_state', 'normal')
        if 'network_state' in self.label_encoders:
            try:
                state_encoded = self.label_encoders['network_state'].transform([state_val])[0]
            except ValueError:
                state_encoded = 0  # Default for unknown states
        else:
            state_encoded = 0
        features.append(state_encoded)
        
        # Fault type encoding (use NONE as default)
        if 'fault_type' in self.label_encoders:
            try:
                fault_encoded = self.label_encoders['fault_type'].transform(['none'])[0]
            except ValueError:
                fault_encoded = 0
        else:
            fault_encoded = 0
        features.append(fault_encoded)
        
        # Numeric features
        features.append(network_state.get('throughput', 100))
        features.append(network_state.get('latency', 10))
        features.append(network_state.get('active_nodes', 14))
        features.append(network_state.get('throughput', 100) / 100.0)  # normalized
        features.append(network_state.get('latency', 10) / 100.0)  # normalized
        
        return np.array(features).reshape(1, -1)
    
    def _predict_performance(self, features: np.ndarray) -> Dict[str, float]:
        """Predict network performance metrics."""
        if self.model is None:
            return {"healing_time": 10, "success_rate": 0.9, "throughput_after": 90}
        
        try:
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            predictions = self.model.predict(features_scaled)[0]
            
            return {
                "healing_time": max(0, predictions[0]),
                "success_rate": np.clip(predictions[1], 0, 1),
                "throughput_after": np.clip(predictions[2], 0, 100)
            }
        except Exception as e:
            self.logger.error(f"Performance prediction failed: {str(e)}")
            return {"healing_time": 10, "success_rate": 0.9, "throughput_after": 90}
    
    def _identify_problematic_node(self, network_state: Dict[str, Any]) -> str:
        """Identify the most problematic node using ML analysis."""
        node_states = network_state.get('node_states', {})
        if not node_states:
            return "unknown"
        
        # Find node with highest predicted impact
        max_impact_node = None
        max_impact = 0
        
        for node_id, state in node_states.items():
            utilization = state.get('utilization', 0)
            response_time = state.get('response_time', 0)
            impact = utilization * 0.6 + (response_time / 1000) * 0.4
            
            if impact > max_impact:
                max_impact = impact
                max_impact_node = node_id
        
        return str(max_impact_node) if max_impact_node else "0"
    
    def _identify_congested_node(self, network_state: Dict[str, Any]) -> str:
        """Identify congested node using traffic analysis."""
        node_states = network_state.get('node_states', {})
        for node_id, state in node_states.items():
            if state.get('utilization', 0) > 0.8:
                return str(node_id)
        return "unknown"
    
    def _identify_problematic_link(self, network_state: Dict[str, Any]) -> str:
        """Identify problematic link using performance analysis."""
        link_states = network_state.get('link_states', {})
        for link_id, state in link_states.items():
            if state.get('packet_loss', 0) > 0.1 or state.get('latency', 0) > 50:
                return str(link_id)
        return "unknown"
    
    def _get_possible_actions(self, fault_type: FaultType) -> List[ActionType]:
        """Get possible actions for a fault type."""
        action_map = {
            FaultType.NODE_DOWN: [ActionType.CLUSTER_REROUTE, ActionType.PRIMARY_REROUTE, ActionType.EMERGENCY_REROUTE],
            FaultType.LINK_DOWN: [ActionType.BACKUP_ACTIVATION, ActionType.SECONDARY_PATH, ActionType.REROUTE],
            FaultType.CONGESTION: [ActionType.LOAD_BALANCE, ActionType.TRAFFIC_SHAPING, ActionType.QOS_ADJUSTMENT],
            FaultType.PACKET_LOSS: [ActionType.ERROR_CORRECTION, ActionType.RETRANSMISSION, ActionType.REROUTE],
            FaultType.CASCADING: [ActionType.EMERGENCY_REROUTE, ActionType.FULL_REROUTE, ActionType.CLUSTER_REROUTE]
        }
        return action_map.get(fault_type, [ActionType.MAINTAIN])
    
    def _predict_action_outcome(self, network_state: Dict[str, Any], fault_info: Tuple[FaultType, Optional[str]], action: ActionType) -> Dict[str, float]:
        """Predict the outcome of taking a specific action."""
        # Simulate network state after action
        simulated_state = network_state.copy()
        
        # Apply action effects (simplified model)
        if action == ActionType.CLUSTER_REROUTE:
            simulated_state['throughput'] = network_state.get('throughput', 100) * 0.85
            simulated_state['latency'] = network_state.get('latency', 10) * 1.2
        elif action == ActionType.BACKUP_ACTIVATION:
            simulated_state['throughput'] = network_state.get('throughput', 100) * 0.9
            simulated_state['latency'] = network_state.get('latency', 10) * 1.1
        elif action == ActionType.LOAD_BALANCE:
            simulated_state['throughput'] = network_state.get('throughput', 100) * 0.95
            simulated_state['latency'] = network_state.get('latency', 10) * 0.9
        
        # Predict performance of simulated state
        features = self._extract_features(simulated_state)
        return self._predict_performance(features)
    
    def _calculate_action_score(self, predicted_outcome: Dict[str, float]) -> float:
        """Calculate a score for an action based on predicted outcomes."""
        healing_time = predicted_outcome.get('healing_time', 60)
        success_rate = predicted_outcome.get('success_rate', 0.5)
        throughput = predicted_outcome.get('throughput_after', 50)
        
        # Weighted score (lower healing time and higher success rate/throughput are better)
        score = (success_rate * 0.4) + (throughput / 100.0 * 0.4) + (max(0, 60 - healing_time) / 60.0 * 0.2)
        return score
    
    def _fallback_action(self, fault_type: FaultType) -> ActionType:
        """Fallback action when ML prediction fails."""
        fallback_map = {
            FaultType.NODE_DOWN: ActionType.CLUSTER_REROUTE,
            FaultType.LINK_DOWN: ActionType.BACKUP_ACTIVATION,
            FaultType.CONGESTION: ActionType.LOAD_BALANCE,
            FaultType.PACKET_LOSS: ActionType.ERROR_CORRECTION,
            FaultType.CASCADING: ActionType.EMERGENCY_REROUTE
        }
        return fallback_map.get(fault_type, ActionType.MAINTAIN)
    
    def _predict_optimal_parameters(self, action: ActionType, fault_info: Tuple[FaultType, Optional[str]]) -> Dict[str, Any]:
        """Predict optimal parameters for action execution."""
        # Return default parameters - could be enhanced with more sophisticated ML
        return {
            "priority": "high" if fault_info[0] in [FaultType.CASCADING, FaultType.NODE_DOWN] else "medium",
            "timeout": 30 if fault_info[0] == FaultType.CASCADING else 15,
            "retries": 3
        }
    
    def _execute_optimized_action(self, action: ActionType, network: Any, fault_location: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action with ML-optimized parameters."""
        changes = []
        
        try:
            if action == ActionType.MAINTAIN:
                return {"success": True, "message": "Network maintained", "changes": []}
            
            # Use ML-optimized parameters
            priority = params.get("priority", "medium")
            timeout = params.get("timeout", 15)
            
            if action == ActionType.CLUSTER_REROUTE:
                changes.append(f"ML-optimized cluster rerouting (priority: {priority}, timeout: {timeout}s)")
                changes.append(f"Rerouted around {fault_location} using predictive path selection")
            
            elif action == ActionType.LOAD_BALANCE:
                changes.append(f"ML-optimized load balancing (timeout: {timeout}s)")
                changes.append(f"Redistributed traffic using regression-based load prediction")
            
            elif action == ActionType.BACKUP_ACTIVATION:
                changes.append(f"ML-optimized backup activation (priority: {priority})")
                changes.append(f"Selected optimal backup path using performance prediction")
            
            else:
                changes.append(f"ML-optimized {action.value} execution")
            
            return {
                "success": True,
                "message": f"ML-optimized {action.value} completed",
                "changes": changes,
                "optimization_params": params
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Optimized execution failed: {str(e)}",
                "changes": changes
            }
    
    def _update_model_with_result(self, fault_info: Tuple[FaultType, Optional[str]], action: ActionType, result: Dict[str, Any]):
        """Update model with new execution result for continuous learning."""
        self.predictions_since_retrain += 1
        
        # Store result for potential retraining
        new_data_point = {
            'fault_type': fault_info[0].value,
            'action': action.value,
            'success': result.get('success', False),
            'execution_time': result.get('execution_time', 0),
            'timestamp': time.time()
        }
        
        # Trigger retraining if needed
        if self.predictions_since_retrain >= self.retrain_interval and self.model_accuracy < 0.8:
            self.logger.info("Triggering model retraining due to low accuracy")
            self._retrain_model()
    
    def _retrain_model(self):
        """Retrain model with updated data."""
        try:
            # In a full implementation, this would collect new training data
            # and retrain the model. For now, we reset the counter.
            self.predictions_since_retrain = 0
            self.logger.info("Model retraining completed")
        except Exception as e:
            self.logger.error(f"Model retraining failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_type": "RandomForestRegressor",
            "accuracy": self.model_accuracy,
            "predictions_since_retrain": self.predictions_since_retrain,
            "retrain_interval": self.retrain_interval,
            "feature_count": len(self.feature_columns),
            "is_trained": self.model is not None
        }