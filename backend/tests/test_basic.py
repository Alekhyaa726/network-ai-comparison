"""
Basic tests for the Triple Network AI Comparison System.
Tests core functionality of agents, services, and API.
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models import RuleBasedAgent, RegressionAgent, RLAgent
from app.services import NetworkManager, FaultInjector, PerformanceMonitor, SimulationEngine

client = TestClient(app)

class TestAgents:
    """Test AI agent functionality."""
    
    def test_rule_based_agent_initialization(self):
        """Test rule-based agent initialization."""
        agent = RuleBasedAgent()
        assert agent.agent_id == "rule_based"
        assert agent.name == "Rule-Based Expert System"
        assert agent.is_active == False
        
        agent.activate()
        assert agent.is_active == True
    
    def test_regression_agent_initialization(self):
        """Test regression agent initialization."""
        agent = RegressionAgent()
        assert agent.agent_id == "regression"
        assert agent.name == "Regression Model Agent"
        
        # Test model info
        model_info = agent.get_model_info()
        assert "model_type" in model_info
        assert "is_trained" in model_info
    
    def test_rl_agent_initialization(self):
        """Test RL agent initialization."""
        agent = RLAgent()
        assert agent.agent_id == "rl"
        assert agent.name == "Reinforcement Learning Agent"
        
        # Test RL metrics
        metrics = agent.get_rl_metrics()
        assert "epsilon" in metrics
        assert "training_steps" in metrics

class TestServices:
    """Test backend services."""
    
    def test_network_manager_initialization(self):
        """Test network manager initialization."""
        network_manager = NetworkManager()
        
        # Check that networks are created for all agents
        assert "rule_based" in network_manager.networks
        assert "regression" in network_manager.networks  
        assert "rl" in network_manager.networks
        
        # Test network state
        state = network_manager.get_network_state("rule_based")
        assert state is not None
        assert "throughput" in state
        assert "latency" in state
    
    def test_fault_injector_initialization(self):
        """Test fault injector initialization."""
        network_manager = NetworkManager()
        fault_injector = FaultInjector(network_manager)
        
        # Check fault types
        fault_types = fault_injector.get_fault_types()
        assert "node_down" in fault_types
        assert "link_down" in fault_types
        assert "congestion" in fault_types
    
    def test_performance_monitor_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor()
        
        # Test KPIs
        kpis = monitor.get_real_time_kpis()
        assert "rule_based" in kpis
        assert "regression" in kpis
        assert "rl" in kpis

class TestAPI:
    """Test REST API endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_system_info_endpoint(self):
        """Test system info endpoint."""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "available_agents" in data
    
    def test_simulation_status_endpoint(self):
        """Test simulation status endpoint."""
        response = client.get("/api/v1/simulation/status")
        assert response.status_code == 200
        data = response.json()
        assert "state" in data
        assert "stats" in data
    
    def test_fault_types_endpoint(self):
        """Test fault types endpoint."""
        response = client.get("/api/v1/faults/types")
        assert response.status_code == 200
        data = response.json()
        assert "fault_types" in data
    
    def test_network_topology_endpoint(self):
        """Test network topology endpoint."""
        response = client.get("/api/v1/network/topology")
        assert response.status_code == 200
        data = response.json()
        assert "topology" in data
    
    def test_agents_status_endpoint(self):
        """Test agents status endpoint."""
        response = client.get("/api/v1/agents/status")
        assert response.status_code == 200
        data = response.json()
        assert "agents_status" in data
    
    def test_performance_kpis_endpoint(self):
        """Test performance KPIs endpoint."""
        response = client.get("/api/v1/performance/kpis")
        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data

class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_simulation_engine_creation(self):
        """Test simulation engine creation and basic functionality."""
        engine = SimulationEngine()
        
        # Test that all components are initialized
        assert engine.network_manager is not None
        assert engine.fault_injector is not None
        assert engine.performance_monitor is not None
        assert len(engine.agents) == 3
    
    def test_fault_injection_flow(self):
        """Test fault injection and agent response flow."""
        engine = SimulationEngine()
        
        # Test manual fault injection
        result = engine.fault_injector.inject_manual_fault("node_down", 5)
        assert result["success"] == True
        assert "fault_id" in result
        
        # Check that fault was applied to all networks
        for agent_id in ["rule_based", "regression", "rl"]:
            network_state = engine.network_manager.get_network_state(agent_id)
            assert network_state is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])