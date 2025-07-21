import React, { useState } from 'react';
import { networkService } from '../services/networkService';

const SimulationLogs = ({ agentLogs }) => {
  const [selectedAgent, setSelectedAgent] = useState('all');
  const [logLevel, setLogLevel] = useState('all');
  const [maxEntries, setMaxEntries] = useState(20);

  const agents = [
    { id: 'rule_based', name: 'Rule-Based', color: '#3b82f6' },
    { id: 'regression', name: 'Regression', color: '#10b981' },
    { id: 'rl', name: 'RL Agent', color: '#f59e0b' }
  ];

  const getLogLevel = (log) => {
    if (log.fault_type === 'fault_injected') return 'warning';
    if (log.success) return 'success';
    if (log.action === 'maintain') return 'info';
    return 'error';
  };

  const getLogIcon = (level) => {
    const icons = {
      'info': 'ℹ️',
      'success': '✅',
      'warning': '⚠️',
      'error': '❌'
    };
    return icons[level] || 'ℹ️';
  };

  const formatLogEntry = (log, agentId) => {
    const timestamp = networkService.formatTimestamp(log.timestamp, 'time');
    const faultType = networkService.formatFaultType(log.fault_type);
    const actionType = networkService.formatActionType(log.action);
    
    if (log.fault_type === 'fault_injected') {
      return `${timestamp} - Fault Injected: ${faultType}`;
    }
    
    return `${timestamp} - ${faultType} → ${actionType} (${log.success ? 'Success' : 'Failed'})`;
  };

  const getAllLogs = () => {
    const allLogs = [];
    
    agents.forEach(agent => {
      const logs = agentLogs[agent.id] || [];
      logs.forEach(log => {
        allLogs.push({
          ...log,
          agentId: agent.id,
          agentName: agent.name,
          agentColor: agent.color
        });
      });
    });

    // Sort by timestamp (newest first)
    allLogs.sort((a, b) => b.timestamp - a.timestamp);
    
    return allLogs.slice(0, maxEntries);
  };

  const getFilteredLogs = () => {
    let logs;
    
    if (selectedAgent === 'all') {
      logs = getAllLogs();
    } else {
      logs = (agentLogs[selectedAgent] || [])
        .slice(0, maxEntries)
        .map(log => ({
          ...log,
          agentId: selectedAgent,
          agentName: agents.find(a => a.id === selectedAgent)?.name,
          agentColor: agents.find(a => a.id === selectedAgent)?.color
        }));
    }

    if (logLevel !== 'all') {
      logs = logs.filter(log => getLogLevel(log) === logLevel);
    }

    return logs;
  };

  const clearLogs = () => {
    // This would need to be implemented to clear logs
    console.log('Clear logs functionality would be implemented here');
  };

  const exportLogs = () => {
    const logs = getFilteredLogs();
    const csvContent = "data:text/csv;charset=utf-8," + 
      "Timestamp,Agent,Fault Type,Action,Success,Message\n" +
      logs.map(log => 
        `${new Date(log.timestamp * 1000).toISOString()},${log.agentName},${log.fault_type},${log.action},${log.success},"${log.message || ''}"`
      ).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `simulation_logs_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const filteredLogs = getFilteredLogs();

  return (
    <div className="simulation-logs">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3>Simulation Logs</h3>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
            onClick={exportLogs}
            disabled={filteredLogs.length === 0}
          >
            💾 Export
          </button>
          <button
            className="btn btn-secondary"
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
            onClick={clearLogs}
          >
            🗑️ Clear
          </button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ 
        display: 'flex', 
        gap: '1rem', 
        marginBottom: '1rem', 
        padding: '0.75rem', 
        background: '#f9fafb', 
        borderRadius: '6px',
        flexWrap: 'wrap'
      }}>
        <div className="form-group">
          <label className="form-label" style={{ fontSize: '0.875rem' }}>Agent</label>
          <select
            className="form-select"
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            style={{ fontSize: '0.875rem', minWidth: '120px' }}
          >
            <option value="all">All Agents</option>
            {agents.map(agent => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" style={{ fontSize: '0.875rem' }}>Level</label>
          <select
            className="form-select"
            value={logLevel}
            onChange={(e) => setLogLevel(e.target.value)}
            style={{ fontSize: '0.875rem', minWidth: '100px' }}
          >
            <option value="all">All Levels</option>
            <option value="info">Info</option>
            <option value="success">Success</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" style={{ fontSize: '0.875rem' }}>Max Entries</label>
          <select
            className="form-select"
            value={maxEntries}
            onChange={(e) => setMaxEntries(parseInt(e.target.value))}
            style={{ fontSize: '0.875rem', minWidth: '80px' }}
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>

      {/* Logs Display */}
      {selectedAgent === 'all' ? (
        // Unified log view
        <div className="log-panel" style={{ maxHeight: '400px', overflow: 'auto' }}>
          <div className="log-header" style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            Unified Logs ({filteredLogs.length} entries)
          </div>
          <div className="log-entries">
            {filteredLogs.length > 0 ? (
              filteredLogs.map((log, index) => {
                const level = getLogLevel(log);
                return (
                  <div key={index} className={`log-entry ${level}`}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span>{getLogIcon(level)}</span>
                      <span 
                        style={{ 
                          fontWeight: '600', 
                          color: log.agentColor,
                          minWidth: '80px'
                        }}
                      >
                        {log.agentName}
                      </span>
                      <span style={{ flex: 1 }}>
                        {formatLogEntry(log, log.agentId)}
                      </span>
                    </div>
                    {log.message && (
                      <div style={{ 
                        marginTop: '0.25rem', 
                        fontSize: '0.7rem', 
                        opacity: 0.8,
                        marginLeft: '2rem'
                      }}>
                        {log.message}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div style={{ 
                padding: '2rem', 
                textAlign: 'center', 
                color: '#6b7280',
                fontSize: '0.875rem'
              }}>
                No log entries found
              </div>
            )}
          </div>
        </div>
      ) : (
        // Agent-specific log view
        <div className="logs-container" style={{ gridTemplateColumns: '1fr' }}>
          <div className="log-panel" style={{ maxHeight: '400px' }}>
            <div className="log-header" style={{ 
              backgroundColor: agents.find(a => a.id === selectedAgent)?.color,
              color: 'white'
            }}>
              {agents.find(a => a.id === selectedAgent)?.name} Logs ({filteredLogs.length} entries)
            </div>
            <div className="log-entries">
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log, index) => {
                  const level = getLogLevel(log);
                  return (
                    <div key={index} className={`log-entry ${level}`}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>{getLogIcon(level)}</span>
                        <span style={{ flex: 1 }}>
                          {formatLogEntry(log, selectedAgent)}
                        </span>
                      </div>
                      {log.message && (
                        <div style={{ 
                          marginTop: '0.25rem', 
                          fontSize: '0.7rem', 
                          opacity: 0.8,
                          marginLeft: '1.5rem'
                        }}>
                          {log.message}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div style={{ 
                  padding: '2rem', 
                  textAlign: 'center', 
                  color: '#6b7280',
                  fontSize: '0.875rem'
                }}>
                  No log entries found for {agents.find(a => a.id === selectedAgent)?.name}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Log Statistics */}
      <div style={{ 
        marginTop: '1rem', 
        padding: '0.75rem', 
        background: '#f9fafb', 
        borderRadius: '6px',
        fontSize: '0.875rem'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem' }}>
          <div>
            <span style={{ color: '#6b7280' }}>Total Entries: </span>
            <span style={{ fontWeight: '600' }}>{filteredLogs.length}</span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Success Rate: </span>
            <span style={{ fontWeight: '600', color: '#10b981' }}>
              {filteredLogs.length > 0 ? 
                `${((filteredLogs.filter(log => log.success).length / filteredLogs.length) * 100).toFixed(1)}%` : 
                '0%'
              }
            </span>
          </div>
          <div>
            <span style={{ color: '#6b7280' }}>Recent Activity: </span>
            <span style={{ fontWeight: '600' }}>
              {filteredLogs.length > 0 ? 
                networkService.formatTimestamp(filteredLogs[0].timestamp, 'relative') : 
                'None'
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimulationLogs;