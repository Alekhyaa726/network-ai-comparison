"""
WebSocket manager for real-time communication.
Handles WebSocket connections and broadcasting simulation updates.
"""
import json
import asyncio
import logging
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.logger = logging.getLogger("websocket_manager")
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = client_info or {}
        
        self.logger.info(f"New WebSocket connection accepted. Total connections: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "message": "Connected to Triple Network AI Comparison System",
            "timestamp": asyncio.get_event_loop().time()
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.active_connections.discard(websocket)
        self.connection_info.pop(websocket, None)
        
        self.logger.info(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            self.logger.error(f"Failed to send personal message: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message, default=str)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                self.logger.error(f"Failed to broadcast to connection: {str(e)}")
                disconnected.add(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_simulation_status(self, status: Dict[str, Any]):
        """Broadcast simulation status update."""
        await self.broadcast({
            "type": "simulation_status",
            "data": status,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_agent_decision(self, agent_id: str, decision_data: Dict[str, Any]):
        """Broadcast agent decision to all clients."""
        await self.broadcast({
            "type": "agent_decision",
            "agent_id": agent_id,
            "data": decision_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_fault_injection(self, fault_data: Dict[str, Any]):
        """Broadcast fault injection event."""
        await self.broadcast({
            "type": "fault_injection",
            "data": fault_data,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_network_state(self, agent_id: str, network_state: Dict[str, Any]):
        """Broadcast network state update."""
        await self.broadcast({
            "type": "network_state",
            "agent_id": agent_id,
            "data": network_state,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_performance_metrics(self, metrics: Dict[str, Any]):
        """Broadcast performance metrics update."""
        await self.broadcast({
            "type": "performance_metrics",
            "data": metrics,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    async def broadcast_comparison_report(self, report: Dict[str, Any]):
        """Broadcast comparison report."""
        await self.broadcast({
            "type": "comparison_report",
            "data": report,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_connections_info(self) -> List[Dict[str, Any]]:
        """Get information about all connections."""
        return [
            {
                "connection_id": id(websocket),
                "info": info,
                "connected_time": info.get("connected_time")
            }
            for websocket, info in self.connection_info.items()
        ]

# Global WebSocket manager instance
websocket_manager = WebSocketManager()