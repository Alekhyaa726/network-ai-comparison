/**
 * Constants used throughout the frontend application.
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  WS_URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000',
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000
};

// Agent Configuration
export const AGENTS = {
  RULE_BASED: {
    id: 'rule_based',
    name: 'Rule-Based Expert System',
    shortName: 'Rule-Based',
    description: 'Uses predefined expert rules and decision trees',
    color: '#3b82f6',
    icon: '🧠'
  },
  REGRESSION: {
    id: 'regression',
    name: 'Regression Model',
    shortName: 'Regression',
    description: 'ML-based predictions with Random Forest',
    color: '#10b981',
    icon: '📊'
  },
  RL: {
    id: 'rl',
    name: 'RL Agent',
    shortName: 'RL Agent',
    description: 'Deep Q-Network with experience replay',
    color: '#f59e0b',
    icon: '🤖'
  }
};

// Network Configuration
export const NETWORK_CONFIG = {
  NSFNET: {
    NODES: 14,
    LINKS: 18,
    NAME: 'NSFNET',
    DESCRIPTION: 'National Science Foundation Network topology'
  },
  VISUALIZATION: {
    WIDTH: 400,
    HEIGHT: 300,
    NODE_RADIUS: 8,
    LINK_WIDTH: 2,
    ANIMATION_DURATION: 300
  }
};

// Fault Types
export const FAULT_TYPES = {
  NODE_DOWN: {
    id: 'node_down',
    name: 'Node Failure',
    description: 'Complete node failure',
    severity: 'high',
    icon: '🔴',
    color: '#ef4444'
  },
  LINK_DOWN: {
    id: 'link_down',
    name: 'Link Failure',
    description: 'Link/connection failure',
    severity: 'medium',
    icon: '📡',
    color: '#f59e0b'
  },
  CONGESTION: {
    id: 'congestion',
    name: 'Network Congestion',
    description: 'Traffic congestion and overload',
    severity: 'medium',
    icon: '🚦',
    color: '#f59e0b'
  },
  PACKET_LOSS: {
    id: 'packet_loss',
    name: 'Packet Loss',
    description: 'Random packet loss',
    severity: 'low',
    icon: '📦',
    color: '#10b981'
  },
  CASCADING: {
    id: 'cascading',
    name: 'Cascading Failure',
    description: 'Progressive failure propagation',
    severity: 'critical',
    icon: '🌊',
    color: '#dc2626'
  }
};

// Performance Metrics
export const METRICS = {
  HEALING_TIME: {
    id: 'healingTime',
    name: 'Healing Time',
    unit: 's',
    description: 'Average time taken to detect and resolve network faults',
    betterWhen: 'lower',
    thresholds: { good: 15, warning: 30 },
    icon: '⏱️'
  },
  RECOVERY_ACCURACY: {
    id: 'recoveryAccuracy',
    name: 'Recovery Accuracy',
    unit: '%',
    description: 'Percentage of successful fault recoveries',
    betterWhen: 'higher',
    thresholds: { good: 85, warning: 70 },
    icon: '🎯'
  },
  NETWORK_THROUGHPUT: {
    id: 'networkThroughput',
    name: 'Network Throughput',
    unit: '%',
    description: 'Current network throughput as percentage of maximum capacity',
    betterWhen: 'higher',
    thresholds: { good: 80, warning: 60 },
    icon: '📈'
  },
  DECISION_TIME: {
    id: 'decisionTime',
    name: 'Decision Time',
    unit: 's',
    description: 'Time taken by the AI agent to make healing decisions',
    betterWhen: 'lower',
    thresholds: { good: 1, warning: 3 },
    icon: '🤔'
  },
  PATH_OPTIMIZATION: {
    id: 'pathOptimization',
    name: 'Path Optimization',
    unit: '%',
    description: 'Effectiveness of routing decisions in maintaining network performance',
    betterWhen: 'higher',
    thresholds: { good: 80, warning: 60 },
    icon: '🛣️'
  },
  RESOURCE_UTILIZATION: {
    id: 'resourceUtilization',
    name: 'Resource Utilization',
    unit: '%',
    description: 'Efficiency of network resource usage during healing operations',
    betterWhen: 'higher',
    thresholds: { good: 75, warning: 50 },
    icon: '⚡'
  },
  DECISION_CONSISTENCY: {
    id: 'decisionConsistency',
    name: 'Decision Consistency',
    unit: '%',
    description: 'Consistency of agent decisions across similar scenarios',
    betterWhen: 'higher',
    thresholds: { good: 85, warning: 70 },
    icon: '🔄'
  }
};

// Simulation States
export const SIMULATION_STATES = {
  STOPPED: {
    id: 'stopped',
    name: 'Stopped',
    color: '#6b7280',
    icon: '⏹️'
  },
  STARTING: {
    id: 'starting',
    name: 'Starting',
    color: '#f59e0b',
    icon: '🔄'
  },
  RUNNING: {
    id: 'running',
    name: 'Running',
    color: '#10b981',
    icon: '▶️'
  },
  PAUSED: {
    id: 'paused',
    name: 'Paused',
    color: '#f59e0b',
    icon: '⏸️'
  },
  STOPPING: {
    id: 'stopping',
    name: 'Stopping',
    color: '#ef4444',
    icon: '⏹️'
  },
  ERROR: {
    id: 'error',
    name: 'Error',
    color: '#ef4444',
    icon: '❌'
  }
};

// Network States
export const NETWORK_STATES = {
  NORMAL: {
    id: 'normal',
    name: 'Normal',
    color: '#10b981',
    description: 'Network operating normally'
  },
  DEGRADED: {
    id: 'degraded',
    name: 'Degraded',
    color: '#f59e0b',
    description: 'Network performance degraded'
  },
  CRITICAL: {
    id: 'critical',
    name: 'Critical',
    color: '#ef4444',
    description: 'Network in critical state'
  },
  UNKNOWN: {
    id: 'unknown',
    name: 'Unknown',
    color: '#6b7280',
    description: 'Network state unknown'
  }
};

// Connection States
export const CONNECTION_STATES = {
  CONNECTED: {
    id: 'connected',
    name: 'Connected',
    color: '#10b981',
    icon: '🟢'
  },
  CONNECTING: {
    id: 'connecting',
    name: 'Connecting',
    color: '#f59e0b',
    icon: '🟡'
  },
  DISCONNECTED: {
    id: 'disconnected',
    name: 'Disconnected',
    color: '#ef4444',
    icon: '🔴'
  }
};

// Log Levels
export const LOG_LEVELS = {
  INFO: {
    id: 'info',
    name: 'Info',
    color: '#3b82f6',
    icon: 'ℹ️'
  },
  SUCCESS: {
    id: 'success',
    name: 'Success',
    color: '#10b981',
    icon: '✅'
  },
  WARNING: {
    id: 'warning',
    name: 'Warning',
    color: '#f59e0b',
    icon: '⚠️'
  },
  ERROR: {
    id: 'error',
    name: 'Error',
    color: '#ef4444',
    icon: '❌'
  }
};

// Update Intervals
export const UPDATE_INTERVALS = {
  FAST: 1000,    // 1 second
  NORMAL: 5000,  // 5 seconds
  SLOW: 10000,   // 10 seconds
  WEBSOCKET_HEARTBEAT: 30000  // 30 seconds
};

// Chart Configuration
export const CHART_CONFIG = {
  COLORS: {
    PRIMARY: '#3b82f6',
    SUCCESS: '#10b981',
    WARNING: '#f59e0b',
    DANGER: '#ef4444',
    SECONDARY: '#6b7280'
  },
  ANIMATION: {
    DURATION: 300,
    EASING: 'ease-in-out'
  }
};

// Export default configuration object
export default {
  API_CONFIG,
  AGENTS,
  NETWORK_CONFIG,
  FAULT_TYPES,
  METRICS,
  SIMULATION_STATES,
  NETWORK_STATES,
  CONNECTION_STATES,
  LOG_LEVELS,
  UPDATE_INTERVALS,
  CHART_CONFIG
};