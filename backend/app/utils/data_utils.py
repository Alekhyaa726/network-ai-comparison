"""
Data utility functions.
Helper functions for data processing, validation, and transformation.
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import logging

class DataUtils:
    """Utility functions for data operations."""
    
    @staticmethod
    def validate_network_state(network_state: Dict[str, Any]) -> bool:
        """Validate network state data structure."""
        required_fields = ['timestamp', 'throughput', 'latency', 'connectivity', 'active_nodes']
        
        for field in required_fields:
            if field not in network_state:
                return False
        
        # Validate data types and ranges
        try:
            timestamp = float(network_state['timestamp'])
            throughput = float(network_state['throughput'])
            latency = float(network_state['latency'])
            connectivity = float(network_state['connectivity'])
            active_nodes = int(network_state['active_nodes'])
            
            # Range validation
            if not (0 <= throughput <= 100):
                return False
            if latency < 0:
                return False
            if not (0 <= connectivity <= 1):
                return False
            if active_nodes < 0:
                return False
                
        except (ValueError, TypeError):
            return False
        
        return True
    
    @staticmethod
    def sanitize_agent_decision(decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize and validate agent decision data."""
        sanitized = {}
        
        # Required fields with defaults
        sanitized['timestamp'] = decision_data.get('timestamp', datetime.now().timestamp())
        sanitized['agent_id'] = str(decision_data.get('agent_id', 'unknown'))
        sanitized['fault_type'] = str(decision_data.get('fault_type', 'none'))
        sanitized['action'] = str(decision_data.get('action', 'maintain'))
        
        # Numeric fields with validation
        try:
            sanitized['decision_time'] = max(0, float(decision_data.get('decision_time', 0)))
        except (ValueError, TypeError):
            sanitized['decision_time'] = 0.0
        
        # Result data
        result = decision_data.get('result', {})
        sanitized['result'] = {
            'success': bool(result.get('success', False)),
            'message': str(result.get('message', '')),
            'execution_time': max(0, float(result.get('execution_time', 0))),
            'changes': list(result.get('changes', []))
        }
        
        return sanitized
    
    @staticmethod
    def aggregate_performance_data(data_points: List[Dict[str, Any]], window_size: int = 10) -> Dict[str, float]:
        """Aggregate performance data over a sliding window."""
        if not data_points:
            return {
                'avg_healing_time': 0.0,
                'avg_decision_time': 0.0,
                'success_rate': 0.0,
                'throughput_trend': 0.0,
                'consistency_score': 0.0
            }
        
        # Take the most recent data points
        recent_data = data_points[-window_size:] if len(data_points) > window_size else data_points
        
        # Extract metrics
        healing_times = []
        decision_times = []
        successes = []
        throughputs = []
        
        for point in recent_data:
            if 'result' in point and 'execution_time' in point['result']:
                healing_times.append(point['result']['execution_time'])
            
            if 'decision_time' in point:
                decision_times.append(point['decision_time'])
            
            if 'result' in point and 'success' in point['result']:
                successes.append(1 if point['result']['success'] else 0)
            
            # Extract throughput if available in network state
            if 'network_state' in point and 'throughput' in point['network_state']:
                throughputs.append(point['network_state']['throughput'])
        
        # Calculate aggregated metrics
        aggregated = {}
        
        aggregated['avg_healing_time'] = np.mean(healing_times) if healing_times else 0.0
        aggregated['avg_decision_time'] = np.mean(decision_times) if decision_times else 0.0
        aggregated['success_rate'] = np.mean(successes) if successes else 0.0
        
        # Throughput trend (positive = improving, negative = declining)
        if len(throughputs) >= 2:
            trend = (throughputs[-1] - throughputs[0]) / len(throughputs)
            aggregated['throughput_trend'] = trend
        else:
            aggregated['throughput_trend'] = 0.0
        
        # Consistency score (inverse of coefficient of variation)
        if len(healing_times) >= 2:
            cv = np.std(healing_times) / np.mean(healing_times) if np.mean(healing_times) > 0 else 1
            aggregated['consistency_score'] = max(0, 1 - cv)
        else:
            aggregated['consistency_score'] = 1.0 if len(healing_times) == 1 else 0.0
        
        return aggregated
    
    @staticmethod
    def format_timestamp(timestamp: float, format_type: str = 'iso') -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            
            if format_type == 'iso':
                return dt.isoformat()
            elif format_type == 'readable':
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            elif format_type == 'time_only':
                return dt.strftime('%H:%M:%S')
            else:
                return str(timestamp)
        except:
            return str(timestamp)
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
        """Export data to CSV file."""
        try:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            logging.error(f"Failed to export to CSV: {str(e)}")
            return False
    
    @staticmethod
    def export_to_json(data: Any, filename: str, indent: int = 2) -> bool:
        """Export data to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=indent, default=str)
            return True
        except Exception as e:
            logging.error(f"Failed to export to JSON: {str(e)}")
            return False
    
    @staticmethod
    def calculate_percentiles(data: List[float], percentiles: List[float] = [25, 50, 75, 90, 95]) -> Dict[str, float]:
        """Calculate percentiles for numerical data."""
        if not data:
            return {f'p{p}': 0.0 for p in percentiles}
        
        result = {}
        for p in percentiles:
            result[f'p{p}'] = np.percentile(data, p)
        
        return result
    
    @staticmethod
    def normalize_metrics(metrics: Dict[str, float], ranges: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Normalize metrics to 0-1 range based on expected ranges."""
        normalized = {}
        
        for metric, value in metrics.items():
            if metric in ranges:
                min_val, max_val = ranges[metric]
                if max_val > min_val:
                    normalized[metric] = (value - min_val) / (max_val - min_val)
                    normalized[metric] = max(0, min(1, normalized[metric]))  # Clamp to [0,1]
                else:
                    normalized[metric] = 0.0
            else:
                normalized[metric] = value
        
        return normalized
    
    @staticmethod
    def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[int]:
        """Detect anomalies using z-score method."""
        if len(data) < 3:
            return []
        
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return []
        
        anomalies = []
        for i, value in enumerate(data):
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                anomalies.append(i)
        
        return anomalies
    
    @staticmethod
    def smooth_time_series(data: List[float], window_size: int = 5) -> List[float]:
        """Apply moving average smoothing to time series data."""
        if len(data) < window_size:
            return data.copy()
        
        smoothed = []
        for i in range(len(data)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(data), i + window_size // 2 + 1)
            window_data = data[start_idx:end_idx]
            smoothed.append(np.mean(window_data))
        
        return smoothed
    
    @staticmethod
    def create_comparison_matrix(agents_data: Dict[str, Dict[str, float]]) -> pd.DataFrame:
        """Create comparison matrix for agents."""
        if not agents_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(agents_data).T
        return df
    
    @staticmethod
    def calculate_correlation_matrix(data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix between different metrics."""
        if not data or len(data) < 2:
            return {}
        
        correlation_matrix = {}
        metrics = list(data.keys())
        
        for metric1 in metrics:
            correlation_matrix[metric1] = {}
            for metric2 in metrics:
                if len(data[metric1]) > 1 and len(data[metric2]) > 1:
                    try:
                        corr = np.corrcoef(data[metric1], data[metric2])[0, 1]
                        correlation_matrix[metric1][metric2] = corr if not np.isnan(corr) else 0.0
                    except:
                        correlation_matrix[metric1][metric2] = 0.0
                else:
                    correlation_matrix[metric1][metric2] = 0.0
        
        return correlation_matrix
    
    @staticmethod
    def generate_summary_statistics(data: List[float]) -> Dict[str, float]:
        """Generate comprehensive summary statistics."""
        if not data:
            return {
                'count': 0, 'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0,
                'median': 0.0, 'q25': 0.0, 'q75': 0.0, 'skewness': 0.0, 'kurtosis': 0.0
            }
        
        data_array = np.array(data)
        
        stats = {
            'count': len(data),
            'mean': float(np.mean(data_array)),
            'std': float(np.std(data_array)),
            'min': float(np.min(data_array)),
            'max': float(np.max(data_array)),
            'median': float(np.median(data_array)),
            'q25': float(np.percentile(data_array, 25)),
            'q75': float(np.percentile(data_array, 75))
        }
        
        # Calculate skewness and kurtosis if scipy is available
        try:
            from scipy import stats as scipy_stats
            stats['skewness'] = float(scipy_stats.skew(data_array))
            stats['kurtosis'] = float(scipy_stats.kurtosis(data_array))
        except ImportError:
            stats['skewness'] = 0.0
            stats['kurtosis'] = 0.0
        
        return stats
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Simple JSON schema validation."""
        errors = []
        
        def validate_field(path: str, value: Any, field_schema: Dict[str, Any]):
            field_type = field_schema.get('type')
            required = field_schema.get('required', False)
            
            if value is None:
                if required:
                    errors.append(f"Required field '{path}' is missing")
                return
            
            # Type checking
            if field_type == 'string' and not isinstance(value, str):
                errors.append(f"Field '{path}' should be string, got {type(value).__name__}")
            elif field_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Field '{path}' should be number, got {type(value).__name__}")
            elif field_type == 'boolean' and not isinstance(value, bool):
                errors.append(f"Field '{path}' should be boolean, got {type(value).__name__}")
            elif field_type == 'array' and not isinstance(value, list):
                errors.append(f"Field '{path}' should be array, got {type(value).__name__}")
            elif field_type == 'object' and not isinstance(value, dict):
                errors.append(f"Field '{path}' should be object, got {type(value).__name__}")
            
            # Range validation for numbers
            if field_type == 'number' and isinstance(value, (int, float)):
                min_val = field_schema.get('minimum')
                max_val = field_schema.get('maximum')
                
                if min_val is not None and value < min_val:
                    errors.append(f"Field '{path}' value {value} is below minimum {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"Field '{path}' value {value} is above maximum {max_val}")
        
        # Validate all fields in schema
        for field_name, field_schema in schema.items():
            field_path = field_name
            field_value = data.get(field_name)
            validate_field(field_path, field_value, field_schema)
        
        return len(errors) == 0, errors