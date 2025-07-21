import React, { useState } from 'react';

const ControlPanel = ({
  simulationState,
  simulationId,
  simulationStats,
  onStartSimulation,
  onStopSimulation,
  onPauseSimulation,
  onResumeSimulation,
  onResetSystem
}) => {
  const [simulationConfig, setSimulationConfig] = useState({
    update_interval: 1.0,
    max_simulation_time: 3600,
    auto_fault_injection: false
  });

  const handleStartSimulation = () => {
    onStartSimulation(simulationConfig);
  };

  const handleConfigChange = (key, value) => {
    setSimulationConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const getStateColor = (state) => {
    const colors = {
      'stopped': '#6b7280',
      'starting': '#f59e0b',
      'running': '#10b981',
      'paused': '#f59e0b',
      'stopping': '#ef4444',
      'error': '#ef4444'
    };
    return colors[state] || '#6b7280';
  };

  const getStateIcon = (state) => {
    const icons = {
      'stopped': '⏹️',
      'starting': '🔄',
      'running': '▶️',
      'paused': '⏸️',
      'stopping': '⏹️',
      'error': '❌'
    };
    return icons[state] || '❓';
  };

  return (
    <div className="control-panel">
      <h3>Simulation Control</h3>
      
      {/* Simulation Status */}
      <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.2rem' }}>{getStateIcon(simulationState)}</span>
            <span style={{ fontWeight: '600', color: getStateColor(simulationState) }}>
              {simulationState.charAt(0).toUpperCase() + simulationState.slice(1)}
            </span>
          </div>
          {simulationId && (
            <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
              ID: {simulationId}
            </span>
          )}
        </div>
        
        {/* Simulation Statistics */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '0.5rem', fontSize: '0.875rem' }}>
          <div>
            <span style={{ color: '#6b7280' }}>Faults: </span>
            <span style={{ fontWeight: '600' }}>{simulationStats.total_faults_injected || 0}</span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Decisions: </span>
            <span style={{ fontWeight: '600' }}>{simulationStats.total_decisions_made || 0}</span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Healing Actions: </span>
            <span style={{ fontWeight: '600' }}>{simulationStats.total_healing_actions || 0}</span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Active Agents: </span>
            <span style={{ fontWeight: '600' }}>{simulationStats.agents_active || 0}</span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Active Faults: </span>
            <span style={{ fontWeight: '600' }}>{simulationStats.current_fault_count || 0}</span>
          </div>
        </div>
      </div>

      {/* Configuration (only show when stopped) */}
      {simulationState === 'stopped' && (
        <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
          <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#374151' }}>Configuration</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem' }}>
            <div className="form-group">
              <label className="form-label">Update Interval (seconds)</label>
              <input
                type="number"
                className="form-input"
                value={simulationConfig.update_interval}
                onChange={(e) => handleConfigChange('update_interval', parseFloat(e.target.value))}
                min="0.1"
                max="10"
                step="0.1"
                style={{ fontSize: '0.875rem' }}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Max Duration (seconds)</label>
              <input
                type="number"
                className="form-input"
                value={simulationConfig.max_simulation_time}
                onChange={(e) => handleConfigChange('max_simulation_time', parseInt(e.target.value))}
                min="60"
                max="7200"
                step="60"
                style={{ fontSize: '0.875rem' }}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Auto Fault Injection</label>
              <select
                className="form-select"
                value={simulationConfig.auto_fault_injection}
                onChange={(e) => handleConfigChange('auto_fault_injection', e.target.value === 'true')}
                style={{ fontSize: '0.875rem' }}
              >
                <option value="false">Disabled</option>
                <option value="true">Enabled</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Control Buttons */}
      <div className="control-buttons">
        {simulationState === 'stopped' && (
          <button 
            className="btn btn-primary"
            onClick={handleStartSimulation}
          >
            <span>▶️</span>
            Start Simulation
          </button>
        )}

        {simulationState === 'running' && (
          <>
            <button 
              className="btn btn-warning"
              onClick={onPauseSimulation}
            >
              <span>⏸️</span>
              Pause
            </button>
            <button 
              className="btn btn-danger"
              onClick={onStopSimulation}
            >
              <span>⏹️</span>
              Stop
            </button>
          </>
        )}

        {simulationState === 'paused' && (
          <>
            <button 
              className="btn btn-success"
              onClick={onResumeSimulation}
            >
              <span>▶️</span>
              Resume
            </button>
            <button 
              className="btn btn-danger"
              onClick={onStopSimulation}
            >
              <span>⏹️</span>
              Stop
            </button>
          </>
        )}

        {(simulationState === 'stopped' || simulationState === 'error') && (
          <button 
            className="btn btn-secondary"
            onClick={onResetSystem}
          >
            <span>🔄</span>
            Reset System
          </button>
        )}

        {/* Status indicators for other states */}
        {(simulationState === 'starting' || simulationState === 'stopping') && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#6b7280' }}>
            <div style={{ 
              width: '16px', 
              height: '16px', 
              border: '2px solid #e5e7eb', 
              borderTop: '2px solid #3b82f6', 
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite' 
            }}></div>
            <span>{simulationState === 'starting' ? 'Starting...' : 'Stopping...'}</span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
        <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#374151' }}>Quick Actions</h4>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button 
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.375rem 0.75rem' }}
            disabled={simulationState !== 'running'}
            onClick={() => window.open('/api/v1/performance/report', '_blank')}
          >
            📊 Export Report
          </button>
          <button 
            className="btn btn-secondary"
            style={{ fontSize: '0.8rem', padding: '0.375rem 0.75rem' }}
            disabled={simulationState !== 'running'}
            onClick={() => window.open('/api/v1/performance/export', '_blank')}
          >
            💾 Export Data
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ControlPanel;