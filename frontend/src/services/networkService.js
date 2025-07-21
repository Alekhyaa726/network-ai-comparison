/**
 * Network service for handling network-related data operations.
 * Provides utilities for network visualization and data processing.
 */

export const networkService = {
  /**
   * Format network state data for display
   */
  formatNetworkState(networkState) {
    if (!networkState) {
      return {
        throughput: 0,
        latency: 0,
        connectivity: 0,
        activeNodes: 0,
        activeLinks: 0,
        networkState: 'unknown'
      };
    }

    return {
      throughput: Math.round((networkState.throughput || 0) * 10) / 10,
      latency: Math.round((networkState.latency || 0) * 10) / 10,
      connectivity: Math.round((networkState.connectivity || 0) * 100),
      activeNodes: networkState.active_nodes || 0,
      activeLinks: networkState.active_links || 0,
      networkState: networkState.network_state || 'unknown',
      packetLoss: Math.round((networkState.packet_loss || 0) * 1000) / 10 // Convert to percentage
    };
  },

  /**
   * Get network state color based on health
   */
  getNetworkStateColor(networkState) {
    if (!networkState) return '#6b7280'; // gray

    switch (networkState.toLowerCase()) {
      case 'normal':
        return '#10b981'; // green
      case 'degraded':
        return '#f59e0b'; // yellow/orange
      case 'critical':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  },

  /**
   * Get agent-specific colors
   */
  getAgentColor(agentId) {
    const colors = {
      'rule_based': '#3b82f6', // blue
      'regression': '#10b981',  // green
      'rl': '#f59e0b'          // orange
    };
    return colors[agentId] || '#6b7280';
  },

  /**
   * Calculate network health score (0-100)
   */
  calculateHealthScore(networkState) {
    if (!networkState) return 0;

    const formatted = this.formatNetworkState(networkState);
    
    // Weight factors for different metrics
    const throughputScore = formatted.throughput; // 0-100
    const connectivityScore = formatted.connectivity; // 0-100
    const latencyScore = Math.max(0, 100 - (formatted.latency - 10) * 2); // Lower latency is better
    const packetLossScore = Math.max(0, 100 - formatted.packetLoss * 10); // Lower packet loss is better

    // Weighted average
    const healthScore = (
      throughputScore * 0.3 +
      connectivityScore * 0.3 +
      latencyScore * 0.2 +
      packetLossScore * 0.2
    );

    return Math.round(Math.max(0, Math.min(100, healthScore)));
  },

  /**
   * Format performance metrics for display
   */
  formatPerformanceMetrics(metrics) {
    if (!metrics) return {};

    const formatted = {};
    
    Object.keys(metrics).forEach(agentId => {
      const agentMetrics = metrics[agentId];
      formatted[agentId] = {
        healingTime: Math.round((agentMetrics.healing_time || 0) * 100) / 100,
        recoveryAccuracy: Math.round((agentMetrics.recovery_accuracy || 0) * 100),
        networkThroughput: Math.round((agentMetrics.network_throughput || 0) * 10) / 10,
        decisionTime: Math.round((agentMetrics.decision_time || 0) * 1000) / 1000,
        pathOptimization: Math.round((agentMetrics.path_optimization || 0) * 100),
        resourceUtilization: Math.round((agentMetrics.resource_utilization || 0) * 100),
        decisionConsistency: Math.round((agentMetrics.decision_consistency || 0) * 100)
      };
    });

    return formatted;
  },

  /**
   * Get metric display configuration
   */
  getMetricConfig() {
    return {
      healingTime: {
        label: 'Healing Time',
        unit: 's',
        format: (value) => `${value}s`,
        betterWhen: 'lower',
        thresholds: { good: 15, warning: 30 }
      },
      recoveryAccuracy: {
        label: 'Recovery Accuracy',
        unit: '%',
        format: (value) => `${value}%`,
        betterWhen: 'higher',
        thresholds: { good: 85, warning: 70 }
      },
      networkThroughput: {
        label: 'Network Throughput',
        unit: '%',
        format: (value) => `${value}%`,
        betterWhen: 'higher',
        thresholds: { good: 80, warning: 60 }
      },
      decisionTime: {
        label: 'Decision Time',
        unit: 's',
        format: (value) => `${value}s`,
        betterWhen: 'lower',
        thresholds: { good: 1, warning: 3 }
      },
      pathOptimization: {
        label: 'Path Optimization',
        unit: '%',
        format: (value) => `${value}%`,
        betterWhen: 'higher',
        thresholds: { good: 80, warning: 60 }
      },
      resourceUtilization: {
        label: 'Resource Utilization',
        unit: '%',
        format: (value) => `${value}%`,
        betterWhen: 'higher',
        thresholds: { good: 75, warning: 50 }
      },
      decisionConsistency: {
        label: 'Decision Consistency',
        unit: '%',
        format: (value) => `${value}%`,
        betterWhen: 'higher',
        thresholds: { good: 85, warning: 70 }
      }
    };
  },

  /**
   * Get metric status color based on value and thresholds
   */
  getMetricStatus(metricKey, value) {
    const config = this.getMetricConfig()[metricKey];
    if (!config || value === null || value === undefined) {
      return 'unknown';
    }

    const { betterWhen, thresholds } = config;
    
    if (betterWhen === 'higher') {
      if (value >= thresholds.good) return 'good';
      if (value >= thresholds.warning) return 'warning';
      return 'critical';
    } else {
      if (value <= thresholds.good) return 'good';
      if (value <= thresholds.warning) return 'warning';
      return 'critical';
    }
  },

  /**
   * Get status color
   */
  getStatusColor(status) {
    const colors = {
      'good': '#10b981',     // green
      'warning': '#f59e0b',  // orange
      'critical': '#ef4444', // red
      'unknown': '#6b7280'   // gray
    };
    return colors[status] || colors.unknown;
  },

  /**
   * Format fault type for display
   */
  formatFaultType(faultType) {
    const faultNames = {
      'none': 'No Fault',
      'node_down': 'Node Failure',
      'link_down': 'Link Failure',
      'congestion': 'Network Congestion',
      'packet_loss': 'Packet Loss',
      'cascading': 'Cascading Failure'
    };
    return faultNames[faultType] || faultType;
  },

  /**
   * Format action type for display
   */
  formatActionType(actionType) {
    const actionNames = {
      'maintain': 'Maintain',
      'reroute_traffic': 'Reroute Traffic',
      'activate_backup_link': 'Activate Backup',
      'emergency_reroute': 'Emergency Reroute',
      'load_balance': 'Load Balance',
      'error_correction': 'Error Correction',
      'cluster_reroute': 'Cluster Reroute',
      'backup_activation': 'Backup Activation',
      'traffic_shaping': 'Traffic Shaping',
      'primary_reroute': 'Primary Reroute',
      'full_reroute': 'Full Reroute',
      'secondary_path': 'Secondary Path',
      'retransmission': 'Retransmission',
      'qos_adjustment': 'QoS Adjustment'
    };
    return actionNames[actionType] || actionType;
  },

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp, format = 'time') {
    if (!timestamp) return '';
    
    const date = new Date(timestamp * 1000); // Convert from seconds to milliseconds
    
    switch (format) {
      case 'time':
        return date.toLocaleTimeString();
      case 'datetime':
        return date.toLocaleString();
      case 'relative':
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (seconds < 60) return `${seconds}s ago`;
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        return date.toLocaleDateString();
      default:
        return date.toLocaleString();
    }
  },

  /**
   * Generate chart data for performance metrics
   */
  generateChartData(performanceMetrics, metricKey) {
    const agents = ['rule_based', 'regression', 'rl'];
    const colors = {
      'rule_based': '#3b82f6',
      'regression': '#10b981',
      'rl': '#f59e0b'
    };

    const data = {
      labels: agents.map(id => this.getAgentDisplayName(id)),
      datasets: [{
        data: agents.map(agentId => {
          const metrics = performanceMetrics[agentId];
          return metrics ? (metrics[metricKey] || 0) : 0;
        }),
        backgroundColor: agents.map(agentId => colors[agentId]),
        borderColor: agents.map(agentId => colors[agentId]),
        borderWidth: 2
      }]
    };

    return data;
  },

  /**
   * Get agent display name
   */
  getAgentDisplayName(agentId) {
    const names = {
      'rule_based': 'Rule-Based',
      'regression': 'Regression',
      'rl': 'RL Agent'
    };
    return names[agentId] || agentId;
  }
};

export default networkService;