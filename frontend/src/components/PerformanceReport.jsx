import React, { useState } from 'react';
import { networkService } from '../services/networkService';

const PerformanceReport = ({ performanceMetrics, simulationState }) => {
  const [selectedMetric, setSelectedMetric] = useState('healingTime');
  const [viewMode, setViewMode] = useState('kpis'); // 'kpis', 'comparison', 'trends'

  const agents = [
    { id: 'rule_based', name: 'Rule-Based', color: '#3b82f6' },
    { id: 'regression', name: 'Regression', color: '#10b981' },
    { id: 'rl', name: 'RL Agent', color: '#f59e0b' }
  ];

  const formatMetrics = () => {
    return networkService.formatPerformanceMetrics(performanceMetrics);
  };

  const getMetricConfig = () => {
    return networkService.getMetricConfig();
  };

  const renderKPICard = (metricKey, config) => {
    const formattedMetrics = formatMetrics();
    
    return (
      <div key={metricKey} className="kpi-card">
        <div className="kpi-title">{config.label}</div>
        <div className="kpi-values">
          {agents.map(agent => {
            const value = formattedMetrics[agent.id]?.[metricKey];
            const status = networkService.getMetricStatus(metricKey, value);
            const statusColor = networkService.getStatusColor(status);
            
            return (
              <div key={agent.id} className="kpi-value">
                <div 
                  className="kpi-number"
                  style={{ color: statusColor }}
                >
                  {value !== undefined ? config.format(value) : '-'}
                </div>
                <div className="kpi-label" style={{ color: agent.color }}>
                  {agent.name}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const renderKPIsView = () => {
    const metricConfig = getMetricConfig();
    
    return (
      <div className="kpi-grid">
        {Object.entries(metricConfig).map(([metricKey, config]) => 
          renderKPICard(metricKey, config)
        )}
      </div>
    );
  };

  const renderComparisonView = () => {
    const formattedMetrics = formatMetrics();
    const metricConfig = getMetricConfig();
    const selectedConfig = metricConfig[selectedMetric];
    
    if (!selectedConfig) return null;

    // Calculate rankings
    const rankings = agents
      .map(agent => ({
        ...agent,
        value: formattedMetrics[agent.id]?.[selectedMetric] || 0
      }))
      .sort((a, b) => {
        if (selectedConfig.betterWhen === 'higher') {
          return b.value - a.value;
        } else {
          return a.value - b.value;
        }
      });

    const getRankIcon = (rank) => {
      const icons = ['🥇', '🥈', '🥉'];
      return icons[rank] || `${rank + 1}`;
    };

    return (
      <div>
        <div style={{ marginBottom: '1rem' }}>
          <label className="form-label">Select Metric for Comparison</label>
          <select
            className="form-select"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            style={{ maxWidth: '300px' }}
          >
            {Object.entries(metricConfig).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '1rem' 
        }}>
          {rankings.map((agent, rank) => {
            const status = networkService.getMetricStatus(selectedMetric, agent.value);
            const statusColor = networkService.getStatusColor(status);
            
            return (
              <div 
                key={agent.id}
                style={{
                  background: 'white',
                  border: `2px solid ${agent.color}`,
                  borderRadius: '8px',
                  padding: '1rem',
                  textAlign: 'center',
                  position: 'relative'
                }}
              >
                <div style={{ 
                  position: 'absolute',
                  top: '-10px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: agent.color,
                  color: 'white',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  fontSize: '0.875rem',
                  fontWeight: '600'
                }}>
                  {getRankIcon(rank)} {agent.name}
                </div>
                
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ 
                    fontSize: '2rem', 
                    fontWeight: 'bold', 
                    color: statusColor,
                    marginBottom: '0.5rem'
                  }}>
                    {selectedConfig.format(agent.value)}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                    {selectedConfig.label}
                  </div>
                  <div style={{
                    marginTop: '0.5rem',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: '600',
                    color: 'white',
                    backgroundColor: statusColor
                  }}>
                    {status.toUpperCase()}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Metric Description */}
        <div style={{
          marginTop: '1rem',
          padding: '1rem',
          background: '#f9fafb',
          borderRadius: '6px',
          fontSize: '0.875rem'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
            About {selectedConfig.label}
          </div>
          <div style={{ color: '#6b7280' }}>
            {getMetricDescription(selectedMetric)}
          </div>
        </div>
      </div>
    );
  };

  const getMetricDescription = (metricKey) => {
    const descriptions = {
      healingTime: 'Average time taken to detect and resolve network faults. Lower values indicate faster response.',
      recoveryAccuracy: 'Percentage of successful fault recoveries. Higher values indicate more reliable healing.',
      networkThroughput: 'Current network throughput as percentage of maximum capacity. Higher values are better.',
      decisionTime: 'Time taken by the AI agent to make healing decisions. Lower values indicate faster processing.',
      pathOptimization: 'Effectiveness of routing decisions in maintaining network performance. Higher values are better.',
      resourceUtilization: 'Efficiency of network resource usage during healing operations. Higher values indicate better optimization.',
      decisionConsistency: 'Consistency of agent decisions across similar scenarios. Higher values indicate more predictable behavior.'
    };
    return descriptions[metricKey] || 'No description available.';
  };

  const renderTrendsView = () => {
    return (
      <div style={{ textAlign: 'center', padding: '2rem', color: '#6b7280' }}>
        <div style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>📈</div>
        <div>Trend analysis would be displayed here</div>
        <div style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
          This feature requires historical data collection over time
        </div>
      </div>
    );
  };

  const renderOverallScore = () => {
    const formattedMetrics = formatMetrics();
    
    // Calculate overall scores for each agent
    const overallScores = agents.map(agent => {
      const metrics = formattedMetrics[agent.id];
      if (!metrics) return { ...agent, score: 0 };
      
      // Weighted scoring (simplified)
      const score = (
        (100 - Math.min(100, metrics.healingTime * 2)) * 0.25 +
        metrics.recoveryAccuracy * 0.25 +
        metrics.networkThroughput * 0.2 +
        (100 - Math.min(100, metrics.decisionTime * 50)) * 0.1 +
        metrics.pathOptimization * 0.1 +
        metrics.resourceUtilization * 0.05 +
        metrics.decisionConsistency * 0.05
      );
      
      return { ...agent, score: Math.max(0, Math.min(100, score)) };
    }).sort((a, b) => b.score - a.score);

    return (
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '1.5rem',
        borderRadius: '8px',
        marginBottom: '1rem'
      }}>
        <h4 style={{ marginBottom: '1rem', textAlign: 'center' }}>Overall Performance Ranking</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          {overallScores.map((agent, index) => (
            <div key={agent.id} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                {index === 0 ? '🏆' : index === 1 ? '🥈' : '🥉'}
              </div>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                {agent.name}
              </div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
                {agent.score.toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const hasData = Object.keys(performanceMetrics).length > 0;

  return (
    <div className="performance-dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3>Performance Dashboard</h3>
        
        {/* View Mode Selector */}
        <div style={{ display: 'flex', gap: '0.25rem' }}>
          {[
            { key: 'kpis', label: '📊 KPIs', title: 'Key Performance Indicators' },
            { key: 'comparison', label: '⚖️ Compare', title: 'Side-by-side Comparison' },
            { key: 'trends', label: '📈 Trends', title: 'Performance Trends' }
          ].map(mode => (
            <button
              key={mode.key}
              className={`btn ${viewMode === mode.key ? 'btn-primary' : 'btn-secondary'}`}
              style={{ fontSize: '0.75rem', padding: '0.375rem 0.75rem' }}
              onClick={() => setViewMode(mode.key)}
              title={mode.title}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {!hasData ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem', 
          background: '#f9fafb', 
          borderRadius: '8px',
          color: '#6b7280'
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>📊</div>
          <div style={{ fontSize: '1.125rem', marginBottom: '0.5rem' }}>No Performance Data</div>
          <div style={{ fontSize: '0.875rem' }}>
            {simulationState === 'stopped' 
              ? 'Start a simulation to see performance metrics'
              : 'Waiting for performance data...'
            }
          </div>
        </div>
      ) : (
        <>
          {/* Overall Score */}
          {renderOverallScore()}
          
          {/* Main Content */}
          {viewMode === 'kpis' && renderKPIsView()}
          {viewMode === 'comparison' && renderComparisonView()}
          {viewMode === 'trends' && renderTrendsView()}
          
          {/* Data Timestamp */}
          <div style={{
            marginTop: '1rem',
            padding: '0.5rem',
            background: '#f9fafb',
            borderRadius: '4px',
            fontSize: '0.75rem',
            color: '#6b7280',
            textAlign: 'center'
          }}>
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </>
      )}
    </div>
  );
};

export default PerformanceReport;