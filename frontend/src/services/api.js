/**
 * API service for communicating with the backend.
 * Handles all REST API calls to the Triple Network AI Comparison System backend.
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // System endpoints
  async getSystemInfo() {
    return await apiClient.get('/system/info');
  },

  async resetSystem() {
    return await apiClient.post('/system/reset');
  },

  // Simulation control endpoints
  async startSimulation(config = {}) {
    return await apiClient.post('/simulation/start', config);
  },

  async stopSimulation() {
    return await apiClient.post('/simulation/stop');
  },

  async pauseSimulation() {
    return await apiClient.post('/simulation/pause');
  },

  async resumeSimulation() {
    return await apiClient.post('/simulation/resume');
  },

  async getSimulationStatus() {
    return await apiClient.get('/simulation/status');
  },

  // Fault injection endpoints
  async injectFault(faultType, target = null, description = '') {
    return await apiClient.post('/faults/inject', {
      fault_type: faultType,
      target: target,
      description: description
    });
  },

  async getFaultTypes() {
    return await apiClient.get('/faults/types');
  },

  async getFaultHistory(limit = 50) {
    return await apiClient.get('/faults/history', {
      params: { limit }
    });
  },

  async injectCascadingScenario() {
    return await apiClient.post('/faults/cascade');
  },

  // Network endpoints
  async getNetworkTopology() {
    return await apiClient.get('/network/topology');
  },

  async getNetworkState(agentId) {
    return await apiClient.get(`/network/state/${agentId}`);
  },

  async getNetworkVisualization(agentId) {
    return await apiClient.get(`/network/visualization/${agentId}`);
  },

  async getNetworkStats() {
    return await apiClient.get('/network/stats');
  },

  // Agent endpoints
  async getAgentsStatus() {
    return await apiClient.get('/agents/status');
  },

  async getAgentLogs(agentId, count = 20) {
    return await apiClient.get(`/agents/${agentId}/logs`, {
      params: { count }
    });
  },

  async getAgentPerformance(agentId) {
    return await apiClient.get(`/agents/${agentId}/performance`);
  },

  // Performance monitoring endpoints
  async getPerformanceKPIs() {
    return await apiClient.get('/performance/kpis');
  },

  async getPerformanceReport() {
    return await apiClient.get('/performance/report');
  },

  async exportPerformanceData() {
    return await apiClient.get('/performance/export');
  }
};

export default apiService;