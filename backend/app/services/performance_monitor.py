"""
Performance Monitor for network simulation.
Collects and analyzes performance metrics for all AI agents and generates reports.
"""
import time
import statistics
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import json
import logging

class PerformanceMonitor:
    """Monitors and analyzes performance of AI agents and network healing."""
    
    def __init__(self, config_path: str = "/app/data/network_configs.json"):
        self.logger = logging.getLogger("performance_monitor")
        self.config_path = config_path
        self.config = {}
        
        # Performance data storage
        self.agent_metrics = {
            'rule_based': defaultdict(list),
            'regression': defaultdict(list), 
            'rl': defaultdict(list)
        }
        
        # Real-time metrics with sliding window
        self.sliding_window_size = 50
        self.real_time_metrics = {
            'rule_based': {
                'healing_times': deque(maxlen=self.sliding_window_size),
                'success_rates': deque(maxlen=self.sliding_window_size),
                'decision_times': deque(maxlen=self.sliding_window_size),
                'throughput_improvements': deque(maxlen=self.sliding_window_size)
            },
            'regression': {
                'healing_times': deque(maxlen=self.sliding_window_size),
                'success_rates': deque(maxlen=self.sliding_window_size),
                'decision_times': deque(maxlen=self.sliding_window_size),
                'throughput_improvements': deque(maxlen=self.sliding_window_size)
            },
            'rl': {
                'healing_times': deque(maxlen=self.sliding_window_size),
                'success_rates': deque(maxlen=self.sliding_window_size),
                'decision_times': deque(maxlen=self.sliding_window_size),
                'throughput_improvements': deque(maxlen=self.sliding_window_size)
            }
        }
        
        # KPI definitions
        self.kpis = [
            'healing_time',
            'recovery_accuracy', 
            'network_throughput',
            'path_optimization',
            'resource_utilization',
            'decision_consistency'
        ]
        
        # Monitoring state
        self.is_monitoring = False
        self.collection_interval = 5  # seconds
        self.monitor_thread = None
        self.session_start_time = None
        self.session_data = {}
        
        # Load configuration
        self._load_config()
        
        # Comparison data
        self.comparison_results = {}
        self.benchmark_thresholds = {
            'healing_time': {'excellent': 10, 'good': 20, 'acceptable': 40},
            'recovery_accuracy': {'excellent': 0.95, 'good': 0.85, 'acceptable': 0.75},
            'network_throughput': {'excellent': 90, 'good': 80, 'acceptable': 70},
            'decision_consistency': {'excellent': 0.9, 'good': 0.8, 'acceptable': 0.7}
        }
    
    def _load_config(self):
        """Load performance monitoring configuration."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            perf_config = self.config.get('performance_metrics', {})
            self.collection_interval = perf_config.get('collection_interval', 5)
            self.kpis = perf_config.get('kpis', self.kpis)
            
            self.logger.info("Performance monitoring configuration loaded")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {str(e)}")
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.is_monitoring:
            return {"success": False, "message": "Monitoring already running"}
        
        self.is_monitoring = True
        self.session_start_time = time.time()
        self.session_data = {
            'start_time': self.session_start_time,
            'agent_decisions': defaultdict(list),
            'fault_recoveries': [],
            'network_states': defaultdict(list)
        }
        
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("Performance monitoring started")
        return {"success": True, "message": "Performance monitoring started"}
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("Performance monitoring stopped")
        return {"success": True, "message": "Performance monitoring stopped"}
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                time.sleep(self.collection_interval)
                
                if not self.is_monitoring:
                    break
                
                # Collect current metrics would happen here
                # In a real implementation, this would gather live metrics
                # from the simulation engine and agents
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(5)
    
    def record_agent_decision(self, agent_id: str, decision_data: Dict[str, Any]):
        """
        Record an agent decision for performance analysis.
        
        Args:
            agent_id: ID of the agent ('rule_based', 'regression', 'rl')
            decision_data: Decision information including timing and results
        """
        if agent_id not in self.agent_metrics:
            return
        
        try:
            # Extract key metrics
            healing_time = decision_data.get('result', {}).get('execution_time', 0)
            decision_time = decision_data.get('decision_time', 0)
            success = decision_data.get('result', {}).get('success', False)
            
            # Store in agent metrics
            self.agent_metrics[agent_id]['healing_times'].append(healing_time)
            self.agent_metrics[agent_id]['decision_times'].append(decision_time)
            self.agent_metrics[agent_id]['successes'].append(1 if success else 0)
            self.agent_metrics[agent_id]['timestamps'].append(time.time())
            
            # Update real-time sliding window
            self.real_time_metrics[agent_id]['healing_times'].append(healing_time)
            self.real_time_metrics[agent_id]['decision_times'].append(decision_time)
            
            # Calculate recent success rate
            recent_successes = list(self.real_time_metrics[agent_id]['success_rates'])
            recent_successes.append(1 if success else 0)
            if len(recent_successes) > self.sliding_window_size:
                recent_successes.pop(0)
            success_rate = sum(recent_successes) / len(recent_successes) if recent_successes else 0
            self.real_time_metrics[agent_id]['success_rates'].append(success_rate)
            
            # Store session data
            if self.is_monitoring:
                self.session_data['agent_decisions'][agent_id].append({
                    'timestamp': time.time(),
                    'fault_type': decision_data.get('fault_type'),
                    'action': decision_data.get('action'),
                    'healing_time': healing_time,
                    'success': success
                })
            
            self.logger.debug(f"Recorded decision for {agent_id}: {healing_time:.2f}s, success: {success}")
            
        except Exception as e:
            self.logger.error(f"Failed to record decision for {agent_id}: {str(e)}")
    
    def record_network_state(self, agent_id: str, network_state: Dict[str, Any]):
        """
        Record network state for performance analysis.
        
        Args:
            agent_id: ID of the agent
            network_state: Current network state data
        """
        if agent_id not in self.agent_metrics:
            return
        
        try:
            # Extract key network metrics
            throughput = network_state.get('throughput', 0)
            latency = network_state.get('latency', 0)
            connectivity = network_state.get('connectivity', 0)
            
            # Store metrics
            self.agent_metrics[agent_id]['throughput'].append(throughput)
            self.agent_metrics[agent_id]['latency'].append(latency)
            self.agent_metrics[agent_id]['connectivity'].append(connectivity)
            
            # Update real-time metrics
            if len(self.real_time_metrics[agent_id]['throughput_improvements']) > 0:
                prev_throughput = self.real_time_metrics[agent_id]['throughput_improvements'][-1]
                improvement = throughput - prev_throughput
            else:
                improvement = 0
            
            self.real_time_metrics[agent_id]['throughput_improvements'].append(throughput)
            
            # Store session data
            if self.is_monitoring:
                self.session_data['network_states'][agent_id].append({
                    'timestamp': time.time(),
                    'throughput': throughput,
                    'latency': latency,
                    'connectivity': connectivity
                })
            
        except Exception as e:
            self.logger.error(f"Failed to record network state for {agent_id}: {str(e)}")
    
    def record_fault_recovery(self, fault_info: Dict[str, Any], recovery_results: Dict[str, Dict[str, Any]]):
        """
        Record fault recovery performance across all agents.
        
        Args:
            fault_info: Information about the injected fault
            recovery_results: Recovery results for each agent
        """
        try:
            recovery_record = {
                'timestamp': time.time(),
                'fault_id': fault_info.get('fault_id'),
                'fault_type': fault_info.get('type'),
                'fault_target': fault_info.get('target'),
                'agent_results': recovery_results,
                'recovery_times': {},
                'success_rates': {}
            }
            
            # Analyze recovery performance
            for agent_id, result in recovery_results.items():
                healing_time = result.get('execution_time', float('inf'))
                success = result.get('success', False)
                
                recovery_record['recovery_times'][agent_id] = healing_time
                recovery_record['success_rates'][agent_id] = 1 if success else 0
            
            # Store in session data
            if self.is_monitoring:
                self.session_data['fault_recoveries'].append(recovery_record)
            
            self.logger.info(f"Recorded fault recovery: {fault_info.get('fault_type')} "
                           f"(agents: {list(recovery_results.keys())})")
            
        except Exception as e:
            self.logger.error(f"Failed to record fault recovery: {str(e)}")
    
    def get_real_time_kpis(self) -> Dict[str, Dict[str, float]]:
        """Get real-time KPIs for all agents."""
        kpis = {}
        
        for agent_id in ['rule_based', 'regression', 'rl']:
            agent_kpis = {}
            
            # Healing time (average of recent healing times)
            healing_times = list(self.real_time_metrics[agent_id]['healing_times'])
            agent_kpis['healing_time'] = statistics.mean(healing_times) if healing_times else 0
            
            # Recovery accuracy (recent success rate)
            success_rates = list(self.real_time_metrics[agent_id]['success_rates'])
            agent_kpis['recovery_accuracy'] = success_rates[-1] if success_rates else 0
            
            # Network throughput (current throughput)
            throughputs = list(self.real_time_metrics[agent_id]['throughput_improvements'])
            agent_kpis['network_throughput'] = throughputs[-1] if throughputs else 0
            
            # Decision time (average recent decision time)
            decision_times = list(self.real_time_metrics[agent_id]['decision_times'])
            agent_kpis['decision_time'] = statistics.mean(decision_times) if decision_times else 0
            
            # Path optimization (based on throughput stability)
            if len(throughputs) >= 5:
                recent_throughputs = throughputs[-5:]
                stability = 1.0 - (statistics.stdev(recent_throughputs) / statistics.mean(recent_throughputs))
                agent_kpis['path_optimization'] = max(0, stability)
            else:
                agent_kpis['path_optimization'] = 0.5
            
            # Resource utilization (efficiency metric)
            if healing_times and decision_times:
                efficiency = 1.0 / (1.0 + statistics.mean(healing_times) * 0.1 + statistics.mean(decision_times) * 0.5)
                agent_kpis['resource_utilization'] = efficiency
            else:
                agent_kpis['resource_utilization'] = 0.5
            
            # Decision consistency (success rate stability)
            if len(success_rates) >= 5:
                consistency = 1.0 - statistics.stdev(success_rates[-5:])
                agent_kpis['decision_consistency'] = max(0, consistency)
            else:
                agent_kpis['decision_consistency'] = agent_kpis['recovery_accuracy']
            
            kpis[agent_id] = agent_kpis
        
        return kpis
    
    def get_agent_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive performance summary for an agent."""
        if agent_id not in self.agent_metrics:
            return {}
        
        metrics = self.agent_metrics[agent_id]
        
        summary = {
            'agent_id': agent_id,
            'total_decisions': len(metrics.get('healing_times', [])),
            'avg_healing_time': 0,
            'avg_decision_time': 0,
            'success_rate': 0,
            'best_healing_time': 0,
            'worst_healing_time': 0,
            'consistency_score': 0,
            'performance_trend': 'stable'
        }
        
        # Calculate statistics
        healing_times = metrics.get('healing_times', [])
        if healing_times:
            summary['avg_healing_time'] = statistics.mean(healing_times)
            summary['best_healing_time'] = min(healing_times)
            summary['worst_healing_time'] = max(healing_times)
        
        decision_times = metrics.get('decision_times', [])
        if decision_times:
            summary['avg_decision_time'] = statistics.mean(decision_times)
        
        successes = metrics.get('successes', [])
        if successes:
            summary['success_rate'] = sum(successes) / len(successes)
        
        # Calculate consistency (lower variance = higher consistency)
        if len(healing_times) >= 3:
            variance = statistics.variance(healing_times)
            mean_time = summary['avg_healing_time']
            summary['consistency_score'] = max(0, 1 - (variance / (mean_time ** 2))) if mean_time > 0 else 0
        
        # Determine performance trend
        if len(healing_times) >= 10:
            recent_avg = statistics.mean(healing_times[-5:])
            earlier_avg = statistics.mean(healing_times[-10:-5])
            
            if recent_avg < earlier_avg * 0.9:
                summary['performance_trend'] = 'improving'
            elif recent_avg > earlier_avg * 1.1:
                summary['performance_trend'] = 'declining'
        
        return summary
    
    def generate_comparison_report(self) -> Dict[str, Any]:
        """Generate comprehensive comparison report across all agents."""
        report = {
            'timestamp': time.time(),
            'session_duration': 0,
            'agent_summaries': {},
            'comparative_analysis': {},
            'rankings': {},
            'recommendations': []
        }
        
        if self.session_start_time:
            report['session_duration'] = time.time() - self.session_start_time
        
        # Get agent summaries
        for agent_id in ['rule_based', 'regression', 'rl']:
            report['agent_summaries'][agent_id] = self.get_agent_performance_summary(agent_id)
        
        # Comparative analysis
        summaries = report['agent_summaries']
        if summaries:
            # Compare healing times
            healing_times = {agent: summary.get('avg_healing_time', float('inf')) 
                           for agent, summary in summaries.items()}
            best_healing = min(healing_times.values())
            
            # Compare success rates
            success_rates = {agent: summary.get('success_rate', 0) 
                           for agent, summary in summaries.items()}
            best_success = max(success_rates.values())
            
            # Compare consistency
            consistency_scores = {agent: summary.get('consistency_score', 0) 
                                for agent, summary in summaries.items()}
            best_consistency = max(consistency_scores.values())
            
            report['comparative_analysis'] = {
                'fastest_healing': min(healing_times, key=healing_times.get),
                'highest_success_rate': max(success_rates, key=success_rates.get),
                'most_consistent': max(consistency_scores, key=consistency_scores.get),
                'healing_time_comparison': healing_times,
                'success_rate_comparison': success_rates,
                'consistency_comparison': consistency_scores
            }
            
            # Generate rankings
            report['rankings'] = self._calculate_rankings(summaries)
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _calculate_rankings(self, summaries: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Calculate agent rankings for different metrics."""
        rankings = {}
        
        # Healing time ranking (lower is better)
        healing_times = [(agent, summary.get('avg_healing_time', float('inf'))) 
                        for agent, summary in summaries.items()]
        healing_times.sort(key=lambda x: x[1])
        rankings['healing_time'] = [agent for agent, _ in healing_times]
        
        # Success rate ranking (higher is better)
        success_rates = [(agent, summary.get('success_rate', 0)) 
                        for agent, summary in summaries.items()]
        success_rates.sort(key=lambda x: x[1], reverse=True)
        rankings['success_rate'] = [agent for agent, _ in success_rates]
        
        # Consistency ranking (higher is better)
        consistency = [(agent, summary.get('consistency_score', 0)) 
                      for agent, summary in summaries.items()]
        consistency.sort(key=lambda x: x[1], reverse=True)
        rankings['consistency'] = [agent for agent, _ in consistency]
        
        # Overall ranking (weighted composite score)
        overall_scores = []
        for agent, summary in summaries.items():
            # Normalize and weight metrics
            healing_score = 1.0 / (1.0 + summary.get('avg_healing_time', 30))  # Lower is better
            success_score = summary.get('success_rate', 0)  # Higher is better
            consistency_score = summary.get('consistency_score', 0)  # Higher is better
            
            composite_score = (healing_score * 0.4 + success_score * 0.4 + consistency_score * 0.2)
            overall_scores.append((agent, composite_score))
        
        overall_scores.sort(key=lambda x: x[1], reverse=True)
        rankings['overall'] = [agent for agent, _ in overall_scores]
        
        return rankings
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on performance analysis."""
        recommendations = []
        
        summaries = report.get('agent_summaries', {})
        analysis = report.get('comparative_analysis', {})
        
        # Analyze healing times
        if 'healing_time_comparison' in analysis:
            healing_times = analysis['healing_time_comparison']
            avg_healing = statistics.mean(healing_times.values()) if healing_times else 0
            
            if avg_healing > 30:
                recommendations.append("Overall healing times are high. Consider optimizing fault detection speed.")
            
            fastest = analysis.get('fastest_healing')
            if fastest:
                recommendations.append(f"The {fastest} agent shows best healing performance. "
                                     f"Study its approach for insights.")
        
        # Analyze success rates
        if 'success_rate_comparison' in analysis:
            success_rates = analysis['success_rate_comparison']
            min_success = min(success_rates.values()) if success_rates else 1
            
            if min_success < 0.8:
                worst_agent = min(success_rates, key=success_rates.get)
                recommendations.append(f"The {worst_agent} agent has low success rate ({min_success:.2f}). "
                                     f"Review its decision logic.")
        
        # Analyze consistency
        if 'consistency_comparison' in analysis:
            consistency = analysis['consistency_comparison']
            min_consistency = min(consistency.values()) if consistency else 1
            
            if min_consistency < 0.7:
                inconsistent_agent = min(consistency, key=consistency.get)
                recommendations.append(f"The {inconsistent_agent} agent shows inconsistent performance. "
                                     f"Consider adjusting its parameters.")
        
        # Agent-specific recommendations
        for agent_id, summary in summaries.items():
            if summary.get('performance_trend') == 'declining':
                recommendations.append(f"The {agent_id} agent performance is declining. "
                                     f"Check for parameter drift or learning issues.")
            
            if agent_id == 'rl' and summary.get('success_rate', 0) < 0.8:
                recommendations.append("RL agent may need more training or exploration tuning.")
            
            if agent_id == 'regression' and summary.get('consistency_score', 0) < 0.7:
                recommendations.append("Regression model may need retraining with more diverse data.")
        
        return recommendations
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export collected metrics in specified format."""
        try:
            export_data = {
                'export_timestamp': time.time(),
                'session_data': self.session_data,
                'agent_metrics': {agent: dict(metrics) for agent, metrics in self.agent_metrics.items()},
                'real_time_kpis': self.get_real_time_kpis(),
                'comparison_report': self.generate_comparison_report()
            }
            
            if format.lower() == 'json':
                return json.dumps(export_data, indent=2, default=str)
            else:
                return str(export_data)
                
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {str(e)}")
            return "{}"
    
    def reset_metrics(self):
        """Reset all collected metrics."""
        for agent_id in self.agent_metrics:
            self.agent_metrics[agent_id].clear()
            for metric_type in self.real_time_metrics[agent_id]:
                self.real_time_metrics[agent_id][metric_type].clear()
        
        self.session_data = {}
        self.comparison_results = {}
        self.session_start_time = None
        
        self.logger.info("All performance metrics reset")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status."""
        return {
            'is_monitoring': self.is_monitoring,
            'session_start_time': self.session_start_time,
            'session_duration': time.time() - self.session_start_time if self.session_start_time else 0,
            'collection_interval': self.collection_interval,
            'total_decisions_recorded': sum(len(metrics.get('healing_times', [])) 
                                          for metrics in self.agent_metrics.values()),
            'agents_monitored': list(self.agent_metrics.keys()),
            'kpis_tracked': self.kpis
        }