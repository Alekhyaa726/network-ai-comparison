import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { networkService } from '../services/networkService';

const FaultInjection = ({ simulationState, onInjectFault }) => {
  const [faultTypes, setFaultTypes] = useState({});
  const [selectedFaultType, setSelectedFaultType] = useState('node_down');
  const [faultTarget, setFaultTarget] = useState('');
  const [faultDescription, setFaultDescription] = useState('');
  const [faultHistory, setFaultHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [autoMode, setAutoMode] = useState(false);

  // Load fault types on mount
  useEffect(() => {
    const loadFaultTypes = async () => {
      try {
        const response = await apiService.getFaultTypes();
        if (response.data && response.data.fault_types) {
          setFaultTypes(response.data.fault_types);
          // Set first fault type as default
          const firstType = Object.keys(response.data.fault_types)[0];
          if (firstType) setSelectedFaultType(firstType);
        }
      } catch (err) {
        console.error('Failed to load fault types:', err);
        setError('Failed to load fault types');
      }
    };

    loadFaultTypes();
  }, []);

  // Load fault history periodically
  useEffect(() => {
    const loadFaultHistory = async () => {
      try {
        const response = await apiService.getFaultHistory(20);
        if (response.data && response.data.fault_history) {
          setFaultHistory(response.data.fault_history);
        }
      } catch (err) {
        console.warn('Failed to load fault history:', err);
      }
    };

    loadFaultHistory();
    
    // Refresh history every 10 seconds when simulation is running
    const interval = simulationState === 'running' ? 
      setInterval(loadFaultHistory, 10000) : null;
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [simulationState]);

  const handleInjectFault = async () => {
    if (!selectedFaultType) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      await onInjectFault(selectedFaultType, faultTarget || null, faultDescription);
      
      // Reset form
      setFaultTarget('');
      setFaultDescription('');
      
      // Refresh history
      setTimeout(async () => {
        try {
          const response = await apiService.getFaultHistory(20);
          if (response.data && response.data.fault_history) {
            setFaultHistory(response.data.fault_history);
          }
        } catch (err) {
          console.warn('Failed to refresh fault history:', err);
        }
      }, 1000);
      
    } catch (err) {
      setError('Failed to inject fault');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCascadingScenario = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.injectCascadingScenario();
      if (!response.data.success) {
        setError(response.data.message);
      }
    } catch (err) {
      setError('Failed to inject cascading scenario');
    } finally {
      setIsLoading(false);
    }
  };

  const getTargetPlaceholder = (faultType) => {
    const placeholders = {
      'node_down': 'Node ID (0-13) or leave empty for random',
      'link_down': 'Link (e.g., 0-1) or leave empty for random',
      'congestion': 'Node ID (0-13) or leave empty for random',
      'packet_loss': 'Leave empty (affects entire network)',
      'cascading': 'Leave empty (multiple targets)'
    };
    return placeholders[faultType] || 'Target identifier or leave empty for random';
  };

  const formatFaultSeverity = (severity) => {
    const colors = {
      'low': '#10b981',
      'medium': '#f59e0b',
      'high': '#ef4444',
      'critical': '#dc2626'
    };
    
    return (
      <span style={{ 
        color: colors[severity] || '#6b7280',
        fontWeight: '600'
      }}>
        {severity?.toUpperCase() || 'UNKNOWN'}
      </span>
    );
  };

  const formatTimeAgo = (timestamp) => {
    return networkService.formatTimestamp(timestamp, 'relative');
  };

  const currentFaultType = faultTypes[selectedFaultType];
  const canInject = simulationState === 'running' && !isLoading;

  return (
    <div className="fault-injection">
      <h3>Fault Injection</h3>

      {error && (
        <div className="error" style={{ marginBottom: '1rem' }}>
          {error}
        </div>
      )}

      {/* Manual Fault Injection */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#374151' }}>
          Manual Fault Injection
        </h4>
        
        <div className="fault-form">
          <div className="form-group">
            <label className="form-label">Fault Type</label>
            <select
              className="form-select"
              value={selectedFaultType}
              onChange={(e) => setSelectedFaultType(e.target.value)}
              disabled={!canInject}
            >
              {Object.entries(faultTypes).map(([key, fault]) => (
                <option key={key} value={key}>
                  {fault.name} ({fault.severity})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Target (Optional)</label>
            <input
              type="text"
              className="form-input"
              value={faultTarget}
              onChange={(e) => setFaultTarget(e.target.value)}
              placeholder={getTargetPlaceholder(selectedFaultType)}
              disabled={!canInject}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Description (Optional)</label>
            <input
              type="text"
              className="form-input"
              value={faultDescription}
              onChange={(e) => setFaultDescription(e.target.value)}
              placeholder="Custom description for this fault"
              disabled={!canInject}
            />
          </div>

          <button
            className="btn btn-danger"
            onClick={handleInjectFault}
            disabled={!canInject}
            style={{ minWidth: '120px' }}
          >
            {isLoading ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div style={{ 
                  width: '12px', 
                  height: '12px', 
                  border: '2px solid transparent', 
                  borderTop: '2px solid white', 
                  borderRadius: '50%', 
                  animation: 'spin 1s linear infinite' 
                }}></div>
                Injecting...
              </span>
            ) : (
              <>⚡ Inject Fault</>
            )}
          </button>
        </div>

        {/* Fault Type Description */}
        {currentFaultType && (
          <div style={{
            marginTop: '0.75rem',
            padding: '0.75rem',
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            fontSize: '0.875rem'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: '600' }}>{currentFaultType.name}</span>
              {formatFaultSeverity(currentFaultType.severity)}
            </div>
            <div style={{ color: '#6b7280', marginBottom: '0.5rem' }}>
              {currentFaultType.description}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              <span>Recovery time: {currentFaultType.recovery_time_range?.[0]}-{currentFaultType.recovery_time_range?.[1]} seconds</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#374151' }}>
          Quick Actions
        </h4>
        
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-warning"
            onClick={handleCascadingScenario}
            disabled={!canInject}
            style={{ fontSize: '0.875rem' }}
          >
            🌊 Cascading Failure
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSelectedFaultType('node_down');
              setFaultTarget('');
              setFaultDescription('Random node failure test');
              handleInjectFault();
            }}
            disabled={!canInject}
            style={{ fontSize: '0.875rem' }}
          >
            🎲 Random Node Failure
          </button>
          
          <button
            className="btn btn-secondary"
            onClick={() => {
              setSelectedFaultType('congestion');
              setFaultTarget('');
              setFaultDescription('Network stress test');
              handleInjectFault();
            }}
            disabled={!canInject}
            style={{ fontSize: '0.875rem' }}
          >
            🚦 Traffic Congestion
          </button>
        </div>
      </div>

      {/* Auto Mode Toggle */}
      <div style={{ marginBottom: '1.5rem' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
          <input
            type="checkbox"
            checked={autoMode}
            onChange={(e) => setAutoMode(e.target.checked)}
            disabled={simulationState !== 'running'}
          />
          <span>Enable automatic fault injection</span>
        </label>
        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '0.25rem' }}>
          When enabled, faults will be injected automatically at random intervals
        </div>
      </div>

      {/* Fault History */}
      <div>
        <h4 style={{ fontSize: '1rem', marginBottom: '0.75rem', color: '#374151' }}>
          Recent Fault History
        </h4>
        
        <div style={{ 
          maxHeight: '300px', 
          overflow: 'auto', 
          border: '1px solid #e5e7eb', 
          borderRadius: '6px' 
        }}>
          {faultHistory.length > 0 ? (
            <div>
              {faultHistory.map((fault, index) => (
                <div 
                  key={fault.fault_id || index}
                  style={{
                    padding: '0.75rem',
                    borderBottom: index < faultHistory.length - 1 ? '1px solid #f3f4f6' : 'none',
                    background: index % 2 === 0 ? '#fafafa' : 'white'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '600', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
                        {networkService.formatFaultType(fault.type)}
                        {fault.target && fault.target !== 'unknown' && (
                          <span style={{ color: '#6b7280', fontWeight: 'normal' }}>
                            {' '}at {fault.target}
                          </span>
                        )}
                      </div>
                      {fault.description && (
                        <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                          {fault.description}
                        </div>
                      )}
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                        Method: {fault.injection_method} • {formatTimeAgo(fault.timestamp)}
                      </div>
                    </div>
                    <div style={{ marginLeft: '1rem' }}>
                      {formatFaultSeverity(fault.severity)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center', 
              color: '#6b7280',
              fontSize: '0.875rem'
            }}>
              No fault injection history
            </div>
          )}
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

export default FaultInjection;