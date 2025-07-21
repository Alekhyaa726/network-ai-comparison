"""
FastAPI routes for the Triple Network AI Comparison System.
Provides REST API endpoints for simulation control and data access.
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import asyncio
import json

from ..services.simulation_engine import SimulationEngine, SimulationState
from ..utils.network_utils import NetworkUtils
from ..utils.data_utils import DataUtils
from .websocket import websocket_manager

# Create router
router = APIRouter()
logger = logging.getLogger("api")

# Global simulation engine instance
simulation_engine = None

def get_simulation_engine() -> SimulationEngine:
    """Get simulation engine instance."""
    global simulation_engine
    if simulation_engine is None:
        simulation_engine = SimulationEngine()
        # Add WebSocket callbacks
        simulation_engine.add_event_callback(_on_simulation_event)
        simulation_engine.add_state_change_callback(_on_state_change)
    return simulation_engine

async def _on_simulation_event(event_data: Dict[str, Any]):
    """Handle simulation events for WebSocket broadcasting."""
    try:
        if event_data['type'] == 'simulation_step':
            await websocket_manager.broadcast_simulation_status(event_data['stats'])
        elif event_data['type'] == 'fault_response':
            await websocket_manager.broadcast_fault_injection(event_data['fault_record'])
    except Exception as e:
        logger.error(f"WebSocket event broadcasting failed: {str(e)}")

async def _on_state_change(new_state: SimulationState):
    """Handle simulation state changes for WebSocket broadcasting."""
    try:
        await websocket_manager.broadcast({
            "type": "simulation_state_change",
            "state": new_state.value,
            "timestamp": asyncio.get_event_loop().time()
        })
    except Exception as e:
        logger.error(f"WebSocket state change broadcasting failed: {str(e)}")

# Pydantic models for request/response
class SimulationConfig(BaseModel):
    update_interval: Optional[float] = 1.0
    max_simulation_time: Optional[int] = 3600
    auto_fault_injection: Optional[bool] = False

class FaultInjectionRequest(BaseModel):
    fault_type: str
    target: Optional[str] = None
    description: Optional[str] = ""

class AgentConfigRequest(BaseModel):
    agent_id: str
    config: Dict[str, Any]

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Triple Network AI Comparison System"}

# Simulation control endpoints
@router.post("/simulation/start")
async def start_simulation(config: Optional[SimulationConfig] = None):
    """Start a new simulation."""
    try:
        engine = get_simulation_engine()
        config_dict = config.dict() if config else None
        result = engine.start_simulation(config_dict)
        
        if result['success']:
            await websocket_manager.broadcast({
                "type": "simulation_started",
                "simulation_id": result['simulation_id'],
                "timestamp": result['start_time']
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to start simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/stop")
async def stop_simulation():
    """Stop the current simulation."""
    try:
        engine = get_simulation_engine()
        result = engine.stop_simulation()
        
        if result['success']:
            await websocket_manager.broadcast({
                "type": "simulation_stopped",
                "simulation_id": result['simulation_id'],
                "duration": result['duration']
            })
        
        return result
    except Exception as e:
        logger.error(f"Failed to stop simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/pause")
async def pause_simulation():
    """Pause the current simulation."""
    try:
        engine = get_simulation_engine()
        result = engine.pause_simulation()
        return result
    except Exception as e:
        logger.error(f"Failed to pause simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/resume")
async def resume_simulation():
    """Resume a paused simulation."""
    try:
        engine = get_simulation_engine()
        result = engine.resume_simulation()
        return result
    except Exception as e:
        logger.error(f"Failed to resume simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/simulation/status")
async def get_simulation_status():
    """Get current simulation status."""
    try:
        engine = get_simulation_engine()
        status = engine.get_simulation_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get simulation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Fault injection endpoints
@router.post("/faults/inject")
async def inject_fault(request: FaultInjectionRequest):
    """Manually inject a fault."""
    try:
        engine = get_simulation_engine()
        result = engine.inject_fault_manually(
            request.fault_type,
            request.target,
            request.description
        )
        
        if result['success']:
            await websocket_manager.broadcast_fault_injection(result['fault_record'])
        
        return result
    except Exception as e:
        logger.error(f"Failed to inject fault: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faults/types")
async def get_fault_types():
    """Get available fault types."""
    try:
        engine = get_simulation_engine()
        fault_types = engine.fault_injector.get_fault_types()
        return {"fault_types": fault_types}
    except Exception as e:
        logger.error(f"Failed to get fault types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/faults/history")
async def get_fault_history(limit: int = 50):
    """Get fault injection history."""
    try:
        engine = get_simulation_engine()
        history = engine.fault_injector.get_fault_history(limit)
        return {"fault_history": history}
    except Exception as e:
        logger.error(f"Failed to get fault history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/faults/cascade")
async def inject_cascading_scenario():
    """Inject a cascading failure scenario."""
    try:
        engine = get_simulation_engine()
        result = engine.fault_injector.inject_cascading_scenario()
        return result
    except Exception as e:
        logger.error(f"Failed to inject cascading scenario: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Network data endpoints
@router.get("/network/topology")
async def get_network_topology():
    """Get the base network topology."""
    try:
        engine = get_simulation_engine()
        topology_data = engine.network_manager.get_topology_data()
        return {"topology": topology_data}
    except Exception as e:
        logger.error(f"Failed to get network topology: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/network/state/{agent_id}")
async def get_network_state(agent_id: str):
    """Get current network state for specific agent."""
    try:
        engine = get_simulation_engine()
        
        if agent_id not in ['rule_based', 'regression', 'rl']:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        network_state = engine.network_manager.get_network_state(agent_id)
        
        if network_state is None:
            raise HTTPException(status_code=404, detail="Network state not found")
        
        return {"agent_id": agent_id, "network_state": network_state}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get network state: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/network/visualization/{agent_id}")
async def get_network_visualization(agent_id: str):
    """Get network data formatted for visualization."""
    try:
        engine = get_simulation_engine()
        
        if agent_id not in ['rule_based', 'regression', 'rl']:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        network = engine.network_manager.get_network(agent_id)
        
        if network is None:
            raise HTTPException(status_code=404, detail="Network not found")
        
        # Get topology data for node positions
        topology_data = engine.network_manager.get_topology_data()
        positions = {}
        if topology_data and 'nodes' in topology_data:
            for node in topology_data['nodes']:
                positions[node['id']] = (node['x'], node['y'])
        
        # Convert to visualization format
        viz_data = NetworkUtils.convert_to_visualization_format(network, positions)
        
        return {
            "agent_id": agent_id,
            "visualization_data": viz_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get network visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/network/stats")
async def get_network_stats():
    """Get network statistics for all agents."""
    try:
        engine = get_simulation_engine()
        stats = engine.network_manager.get_network_stats()
        return {"network_stats": stats}
    except Exception as e:
        logger.error(f"Failed to get network stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Agent endpoints
@router.get("/agents/status")
async def get_agents_status():
    """Get status of all AI agents."""
    try:
        engine = get_simulation_engine()
        status = engine.get_simulation_status()
        return {"agents_status": status.get('agents_status', {})}
    except Exception as e:
        logger.error(f"Failed to get agents status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/logs")
async def get_agent_logs(agent_id: str, count: int = 20):
    """Get recent decision logs for specific agent."""
    try:
        engine = get_simulation_engine()
        
        if agent_id not in ['rule_based', 'regression', 'rl']:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        logs = engine.get_agent_logs(agent_id, count)
        return {"agent_id": agent_id, "logs": logs}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent logs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """Get performance summary for specific agent."""
    try:
        engine = get_simulation_engine()
        
        if agent_id not in ['rule_based', 'regression', 'rl']:
            raise HTTPException(status_code=400, detail="Invalid agent ID")
        
        performance = engine.performance_monitor.get_agent_performance_summary(agent_id)
        return {"agent_id": agent_id, "performance": performance}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent performance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance monitoring endpoints
@router.get("/performance/kpis")
async def get_real_time_kpis():
    """Get real-time KPIs for all agents."""
    try:
        engine = get_simulation_engine()
        kpis = engine.get_real_time_kpis()
        return {"kpis": kpis}
    except Exception as e:
        logger.error(f"Failed to get real-time KPIs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/report")
async def get_performance_report():
    """Generate comprehensive performance comparison report."""
    try:
        engine = get_simulation_engine()
        report = engine.generate_performance_report()
        return {"report": report}
    except Exception as e:
        logger.error(f"Failed to generate performance report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance/export")
async def export_performance_data():
    """Export all simulation data for analysis."""
    try:
        engine = get_simulation_engine()
        data = engine.export_simulation_data()
        return {"export_data": data}
    except Exception as e:
        logger.error(f"Failed to export performance data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_manager.connect(websocket, {
        "connected_time": asyncio.get_event_loop().time(),
        "type": "frontend_client"
    })
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get('type')
                
                # Handle different message types
                if message_type == 'ping':
                    await websocket_manager.send_personal_message({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }, websocket)
                
                elif message_type == 'subscribe_updates':
                    # Client wants to subscribe to specific updates
                    subscriptions = message.get('subscriptions', [])
                    # Store subscription preferences (could be extended)
                    websocket_manager.connection_info[websocket]['subscriptions'] = subscriptions
                
                elif message_type == 'request_status':
                    # Client requesting current status
                    engine = get_simulation_engine()
                    status = engine.get_simulation_status()
                    await websocket_manager.send_personal_message({
                        "type": "simulation_status",
                        "data": status,
                        "timestamp": asyncio.get_event_loop().time()
                    }, websocket)
                
            except json.JSONDecodeError:
                await websocket_manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": asyncio.get_event_loop().time()
                }, websocket)
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        websocket_manager.disconnect(websocket)

# Additional utility endpoints
@router.get("/system/info")
async def get_system_info():
    """Get system information."""
    try:
        engine = get_simulation_engine()
        
        return {
            "system": "Triple Network AI Comparison System",
            "version": "1.0.0",
            "simulation_engine": {
                "state": engine.state.value,
                "simulation_id": engine.simulation_id
            },
            "websocket_connections": websocket_manager.get_connection_count(),
            "available_agents": ["rule_based", "regression", "rl"],
            "available_fault_types": list(engine.fault_injector.get_fault_types().keys())
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system/reset")
async def reset_system():
    """Reset the entire system."""
    try:
        engine = get_simulation_engine()
        
        # Stop simulation if running
        if engine.state != SimulationState.STOPPED:
            engine.stop_simulation()
        
        # Reset all components
        engine.network_manager.reset_all_networks()
        engine.performance_monitor.reset_metrics()
        engine.fault_injector.clear_fault_history()
        
        for agent in engine.agents.values():
            agent.reset_metrics()
        
        await websocket_manager.broadcast({
            "type": "system_reset",
            "timestamp": asyncio.get_event_loop().time()
        })
        
        return {"success": True, "message": "System reset completed"}
    except Exception as e:
        logger.error(f"Failed to reset system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))