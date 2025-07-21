import React from 'react';
import NetworkVisualization from './NetworkVisualization';
import { networkService } from '../services/networkService';

const TripleNetworkView = ({ networkStates, simulationState }) => {
  const agents = [
    { 
      id: 'rule_based', 
      name: 'Rule-Based Expert System',
      description: 'Uses predefined expert rules and decision trees',
      color: '#3b82f6'
    },
    { 
      id: 'regression', 
      name: 'Regression Model',
      description: 'ML-based predictions with Random Forest',
      color: '#10b981'
    },
    { 
      id: 'rl', 
      name: 'RL Agent',
      description: 'Deep Q-Network with experience replay',
      color: '#f59e0b'
    }
  ];

  const formatNetworkStats = (networkState) => {
    if (!networkState) {
      return {
        throughput: '0%',
        latency: '0ms',
        connectivity: '0%',
        activeNodes: '0/14',
        activeLinks: '0/18',
        health: 0,
        status: 'unknown'
      };
    }

    const formatted = networkService.formatNetworkState(networkState);
    return {
      throughput: `${formatted.throughput}%`,
      latency: `${formatted.latency}ms`,
      connectivity: `${formatted.connectivity}%`,
      activeNodes: `${formatted.activeNodes}/14`,
      activeLinks: `${formatted.activeLinks}/18`,
      health: networkService.calculateHealthScore(networkState),
      status: formatted.networkState
    };
  };

  const getStatusBadge = (status) => {
    const color = networkService.getNetworkStateColor({ network_state: status });
    return (
      <span 
        style={{
          display: 'inline-block',
          padding: '0.25rem 0.5rem',
          fontSize: '0.75rem',
          fontWeight: '600',
          borderRadius: '9999px',
          color: 'white',
          backgroundColor: color
        }}
      >
        {status.toUpperCase()}
      </span>
    );
  };

  const getHealthBar = (health) => {
    const getHealthColor = (value) => {
      if (value >= 80) return '#10b981'; // green
      if (value >= 60) return '#f59e0b'; // orange
      return '#ef4444'; // red
    };

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <div style={{
          width: '100px',
          height: '8px',
          backgroundColor: '#e5e7eb',
          borderRadius: '4px',
          overflow: 'hidden'
        }}>
          <div 
            style={{
              width: `${health}%`,
              height: '100%',
              backgroundColor: getHealthColor(health),
              transition: 'width 0.3s ease'
            }}
          />
        </div>
        <span style={{ fontSize: '0.875rem', fontWeight: '600' }}>
          {health}%
        </span>
      </div>
    );
  };

  return (
    <div className="triple-network-container">
      {agents.map(agent => {
        const networkState = networkStates[agent.id];
        const stats = formatNetworkStats(networkState);
        
        return (
          <div key={agent.id} className={`network-panel ${agent.id}`}>
            {/* Header */}
            <div style={{ marginBottom: '1rem' }}>
              <h3 style={{ color: agent.color, marginBottom: '0.25rem' }}>
                {agent.name}
              </h3>
              <p style={{ 
                fontSize: '0.875rem', 
                color: '#6b7280', 
                marginBottom: '0.5rem',
                lineHeight: '1.4'
              }}>
                {agent.description}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                {getStatusBadge(stats.status)}
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                    Network Health
                  </div>
                  {getHealthBar(stats.health)}
                </div>
              </div>
            </div>

            {/* Network Visualization */}
            <NetworkVisualization
              agentId={agent.id}
              networkState={networkState}
              simulationState={simulationState}
              color={agent.color}
            />

            {/* Network Statistics */}
            <div className="network-stats" style={{ marginTop: '1rem' }}>
              <div className="stat-item">
                <span className="stat-label">Throughput</span>
                <span className="stat-value" style={{ color: agent.color }}>
                  {stats.throughput}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Latency</span>
                <span className="stat-value">
                  {stats.latency}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Connectivity</span>
                <span className="stat-value">
                  {stats.connectivity}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Packet Loss</span>
                <span className="stat-value">
                  {networkState ? `${(networkState.packet_loss * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Nodes</span>
                <span className="stat-value">
                  {stats.activeNodes}
                </span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Active Links</span>
                <span className="stat-value">
                  {stats.activeLinks}
                </span>
              </div>
            </div>

            {/* Agent-specific Metrics */}
            <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
              <h5 style={{ 
                fontSize: '0.875rem', 
                fontWeight: '600', 
                marginBottom: '0.5rem',
                color: '#374151'
              }}>
                AI Performance
              </h5>
              
              {simulationState === 'running' && networkState ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
                  <div>
                    <span style={{ color: '#6b7280' }}>Last Update: </span>
                    <span style={{ fontWeight: '500' }}>
                      {networkService.formatTimestamp(networkState.timestamp, 'time')}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#6b7280' }}>Response: </span>
                    <span style={{ fontWeight: '500', color: stats.health > 70 ? '#10b981' : '#ef4444' }}>
                      {stats.health > 70 ? 'Good' : 'Poor'}
                    </span>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: '0.875rem', color: '#6b7280', textAlign: 'center', padding: '1rem' }}>
                  {simulationState === 'stopped' ? 'Start simulation to see metrics' : 'Waiting for data...'}
                </div>
              )}
            </div>

            {/* Quick Actions for this Agent */}
            <div style={{ marginTop: '1rem' }}>
              <div style={{ display: 'flex', gap: '0.25rem' }}>
                <button
                  className="btn btn-secondary"
                  style={{ 
                    fontSize: '0.75rem', 
                    padding: '0.25rem 0.5rem',
                    opacity: simulationState === 'running' ? 1 : 0.5
                  }}
                  disabled={simulationState !== 'running'}
                  onClick={() => {
                    // Could trigger agent-specific actions
                    console.log(`Action for ${agent.id}`);
                  }}
                >
                  📊 Details
                </button>
                <button
                  className="btn btn-secondary"
                  style={{ 
                    fontSize: '0.75rem', 
                    padding: '0.25rem 0.5rem',
                    opacity: simulationState === 'running' ? 1 : 0.5
                  }}
                  disabled={simulationState !== 'running'}
                  onClick={() => {
                    // Could show agent logs
                    console.log(`Logs for ${agent.id}`);
                  }}
                >
                  📝 Logs
                </button>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default TripleNetworkView;