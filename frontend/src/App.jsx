import React, { useState, useEffect, useCallback } from 'react';
import TripleNetworkView from './components/TripleNetworkView';
import ControlPanel from './components/ControlPanel';
import PerformanceReport from './components/PerformanceReport';
import SimulationLogs from './components/SimulationLogs';
import FaultInjection from './components/FaultInjection';
import { websocketService } from './services/websocket';
import { apiService } from './services/api';

function App() {
  // State management
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [simulationState, setSimulationState] = useState('stopped');
  const [simulationId, setSimulationId] = useState(null);
  const [networkStates, setNetworkStates] = useState({
    rule_based: null,
    regression: null,
    rl: null
  });
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [agentLogs, setAgentLogs] = useState({
    rule_based: [],
    regression: [],
    rl: []
  });
  const [simulationStats, setSimulationStats] = useState({
    total_faults_injected: 0,
    total_decisions_made: 0,
    total_healing_actions: 0,
    agents_active: 0,
    current_fault_count: 0
  });
  const [error, setError] = useState(null);

  // WebSocket event handlers
  const handleWebSocketMessage = useCallback((data) => {
    try {
      switch (data.type) {
        case 'connection_established':
          setConnectionStatus('connected');
          setError(null);
          break;
          
        case 'simulation_status':
          setSimulationStats(data.data);
          break;
          
        case 'simulation_state_change':
          setSimulationState(data.state);
          break;
          
        case 'simulation_started':
          setSimulationId(data.simulation_id);
          setSimulationState('running');
          break;
          
        case 'simulation_stopped':
          setSimulationState('stopped');
          break;
          
        case 'agent_decision':
          // Add agent decision to logs
          const agentId = data.agent_id;
          const decision = {
            timestamp: data.timestamp,
            fault_type: data.data.fault_type,
            action: data.data.action,
            success: data.data.result?.success || false,
            message: data.data.result?.message || ''
          };
          
          setAgentLogs(prev => ({
            ...prev,
            [agentId]: [decision, ...prev[agentId]].slice(0, 50) // Keep last 50 entries
          }));
          break;
          
        case 'network_state':
          setNetworkStates(prev => ({
            ...prev,
            [data.agent_id]: data.data
          }));
          break;
          
        case 'performance_metrics':
          setPerformanceMetrics(data.data);
          break;
          
        case 'fault_injection':
          // Add fault injection to logs for all agents
          const faultLog = {
            timestamp: data.timestamp,
            fault_type: data.data.type,
            action: 'fault_injected',
            success: true,
            message: `Fault injected: ${data.data.type} at ${data.data.target}`
          };
          
          setAgentLogs(prev => ({
            rule_based: [faultLog, ...prev.rule_based].slice(0, 50),
            regression: [faultLog, ...prev.regression].slice(0, 50),
            rl: [faultLog, ...prev.rl].slice(0, 50)
          }));
          break;
          
        case 'system_reset':
          // Reset all state
          setNetworkStates({
            rule_based: null,
            regression: null,
            rl: null
          });
          setAgentLogs({
            rule_based: [],
            regression: [],
            rl: []
          });
          setPerformanceMetrics({});
          setSimulationStats({
            total_faults_injected: 0,
            total_decisions_made: 0,
            total_healing_actions: 0,
            agents_active: 0,
            current_fault_count: 0
          });
          break;
          
        default:
          console.log('Unknown WebSocket message type:', data.type);
      }
    } catch (error) {
      console.error('Error handling WebSocket message:', error);
      setError('Error processing real-time update');
    }
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    setConnectionStatus('connecting');
    
    const handleConnect = () => {
      setConnectionStatus('connected');
      setError(null);
    };

    const handleDisconnect = () => {
      setConnectionStatus('disconnected');
    };

    const handleError = (error) => {
      setConnectionStatus('disconnected');
      setError(`Connection error: ${error.message || 'Unknown error'}`);
    };

    // Connect to WebSocket
    websocketService.connect({
      onMessage: handleWebSocketMessage,
      onConnect: handleConnect,
      onDisconnect: handleDisconnect,
      onError: handleError
    });

    // Load initial data
    loadInitialData();

    // Cleanup on unmount
    return () => {
      websocketService.disconnect();
    };
  }, [handleWebSocketMessage]);

  // Load initial data from API
  const loadInitialData = async () => {
    try {
      // Get simulation status
      const statusResponse = await apiService.getSimulationStatus();
      if (statusResponse.data) {
        setSimulationState(statusResponse.data.state);
        setSimulationId(statusResponse.data.simulation_id);
        setSimulationStats(statusResponse.data.stats);
      }

      // Get network states for all agents
      const agents = ['rule_based', 'regression', 'rl'];
      for (const agentId of agents) {
        try {
          const networkResponse = await apiService.getNetworkState(agentId);
          if (networkResponse.data) {
            setNetworkStates(prev => ({
              ...prev,
              [agentId]: networkResponse.data.network_state
            }));
          }
        } catch (error) {
          console.warn(`Failed to load network state for ${agentId}:`, error);
        }
      }

      // Get performance metrics
      try {
        const metricsResponse = await apiService.getPerformanceKPIs();
        if (metricsResponse.data) {
          setPerformanceMetrics(metricsResponse.data.kpis);
        }
      } catch (error) {
        console.warn('Failed to load performance metrics:', error);
      }

    } catch (error) {
      console.error('Failed to load initial data:', error);
      setError('Failed to load initial data');
    }
  };

  // Handle simulation control
  const handleStartSimulation = async (config) => {
    try {
      setError(null);
      const response = await apiService.startSimulation(config);
      if (response.data.success) {
        setSimulationId(response.data.simulation_id);
        setSimulationState('running');
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to start simulation');
      console.error('Start simulation error:', error);
    }
  };

  const handleStopSimulation = async () => {
    try {
      setError(null);
      const response = await apiService.stopSimulation();
      if (response.data.success) {
        setSimulationState('stopped');
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to stop simulation');
      console.error('Stop simulation error:', error);
    }
  };

  const handlePauseSimulation = async () => {
    try {
      setError(null);
      const response = await apiService.pauseSimulation();
      if (!response.data.success) {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to pause simulation');
      console.error('Pause simulation error:', error);
    }
  };

  const handleResumeSimulation = async () => {
    try {
      setError(null);
      const response = await apiService.resumeSimulation();
      if (!response.data.success) {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to resume simulation');
      console.error('Resume simulation error:', error);
    }
  };

  // Handle fault injection
  const handleInjectFault = async (faultType, target, description) => {
    try {
      setError(null);
      const response = await apiService.injectFault(faultType, target, description);
      if (!response.data.success) {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to inject fault');
      console.error('Fault injection error:', error);
    }
  };

  // Handle system reset
  const handleResetSystem = async () => {
    try {
      setError(null);
      const response = await apiService.resetSystem();
      if (response.data.success) {
        // State will be reset via WebSocket message
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      setError('Failed to reset system');
      console.error('System reset error:', error);
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div>
            <h1 className="app-title">Triple Network AI Comparison System</h1>
            <p className="app-subtitle">
              Real-time comparison of AI approaches to network self-healing
            </p>
          </div>
          <div className="connection-status">
            <div className={`status-indicator status-${connectionStatus}`}></div>
            <span>
              {connectionStatus === 'connected' && 'Connected'}
              {connectionStatus === 'connecting' && 'Connecting...'}
              {connectionStatus === 'disconnected' && 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Error Display */}
        {error && (
          <div className="error fade-in">
            {error}
            <button 
              onClick={() => setError(null)}
              style={{ float: 'right', background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
            >
              ×
            </button>
          </div>
        )}

        {/* Control Panel */}
        <ControlPanel
          simulationState={simulationState}
          simulationId={simulationId}
          simulationStats={simulationStats}
          onStartSimulation={handleStartSimulation}
          onStopSimulation={handleStopSimulation}
          onPauseSimulation={handlePauseSimulation}
          onResumeSimulation={handleResumeSimulation}
          onResetSystem={handleResetSystem}
        />

        {/* Triple Network Visualization */}
        <TripleNetworkView
          networkStates={networkStates}
          simulationState={simulationState}
        />

        {/* Performance Dashboard */}
        <PerformanceReport
          performanceMetrics={performanceMetrics}
          simulationState={simulationState}
        />

        {/* Fault Injection Panel */}
        <FaultInjection
          simulationState={simulationState}
          onInjectFault={handleInjectFault}
        />

        {/* Simulation Logs */}
        <SimulationLogs
          agentLogs={agentLogs}
        />
      </main>
    </div>
  );
}

export default App;