import React, { useEffect, useRef, useState } from 'react';
import { apiService } from '../services/api';

const NetworkVisualization = ({ agentId, networkState, simulationState, color }) => {
  const svgRef = useRef(null);
  const [topologyData, setTopologyData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load topology data on mount
  useEffect(() => {
    const loadTopology = async () => {
      try {
        setIsLoading(true);
        const response = await apiService.getNetworkTopology();
        if (response.data && response.data.topology) {
          setTopologyData(response.data.topology);
        }
        setError(null);
      } catch (err) {
        console.error('Failed to load topology:', err);
        setError('Failed to load network topology');
      } finally {
        setIsLoading(false);
      }
    };

    loadTopology();
  }, []);

  // Simple SVG-based network visualization
  useEffect(() => {
    if (!topologyData || !svgRef.current) return;

    const svg = svgRef.current;
    const { nodes, links } = topologyData;
    
    // Clear previous content
    svg.innerHTML = '';

    // SVG dimensions
    const width = 380;
    const height = 280;
    
    // Set SVG attributes
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);

    // Scale factor for positioning
    const scaleX = width / 500;
    const scaleY = height / 300;

    // Draw links first (so they appear behind nodes)
    links.forEach(link => {
      const sourceNode = nodes.find(n => n.id === link.source);
      const targetNode = nodes.find(n => n.id === link.target);
      
      if (sourceNode && targetNode) {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', sourceNode.x * scaleX);
        line.setAttribute('y1', sourceNode.y * scaleY);
        line.setAttribute('x2', targetNode.x * scaleX);
        line.setAttribute('y2', targetNode.y * scaleY);
        
        // Link styling based on status
        const linkState = networkState?.link_states?.[`${link.source}-${link.target}`];
        const isActive = linkState?.status === 'active' || !linkState;
        const utilization = linkState?.utilization || 0;
        
        line.setAttribute('stroke', isActive ? color : '#ef4444');
        line.setAttribute('stroke-width', isActive ? Math.max(1, utilization * 4 + 1) : 1);
        line.setAttribute('stroke-opacity', isActive ? 0.8 : 0.3);
        line.setAttribute('stroke-dasharray', isActive ? 'none' : '5,5');
        
        svg.appendChild(line);
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      
      // Node circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', node.x * scaleX);
      circle.setAttribute('cy', node.y * scaleY);
      circle.setAttribute('r', 8);
      
      // Node styling based on status
      const nodeState = networkState?.node_states?.[node.id.toString()];
      const isActive = nodeState?.status === 'active' || !nodeState;
      const utilization = nodeState?.utilization || 0;
      
      circle.setAttribute('fill', isActive ? color : '#ef4444');
      circle.setAttribute('fill-opacity', isActive ? 0.8 : 0.5);
      circle.setAttribute('stroke', isActive ? '#ffffff' : '#ef4444');
      circle.setAttribute('stroke-width', 2);
      
      // Add pulse animation for high utilization
      if (isActive && utilization > 0.7) {
        const animate = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
        animate.setAttribute('attributeName', 'r');
        animate.setAttribute('values', '8;12;8');
        animate.setAttribute('dur', '2s');
        animate.setAttribute('repeatCount', 'indefinite');
        circle.appendChild(animate);
      }
      
      group.appendChild(circle);
      
      // Node label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', node.x * scaleX);
      text.setAttribute('y', node.y * scaleY - 12);
      text.setAttribute('text-anchor', 'middle');
      text.setAttribute('font-size', '10');
      text.setAttribute('font-weight', '500');
      text.setAttribute('fill', '#374151');
      text.textContent = node.id;
      group.appendChild(text);
      
      // Tooltip for node information
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      title.textContent = `Node ${node.id}: ${node.name}\nStatus: ${isActive ? 'Active' : 'Down'}\nUtilization: ${(utilization * 100).toFixed(1)}%`;
      group.appendChild(title);
      
      svg.appendChild(group);
    });

    // Add legend
    const legend = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    legend.setAttribute('transform', 'translate(10, 10)');
    
    // Legend background
    const legendBg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    legendBg.setAttribute('x', 0);
    legendBg.setAttribute('y', 0);
    legendBg.setAttribute('width', 120);
    legendBg.setAttribute('height', 60);
    legendBg.setAttribute('fill', 'rgba(255,255,255,0.9)');
    legendBg.setAttribute('stroke', '#e5e7eb');
    legendBg.setAttribute('stroke-width', 1);
    legendBg.setAttribute('rx', 4);
    legend.appendChild(legendBg);
    
    // Legend items
    const legendItems = [
      { label: 'Active Node', color: color, y: 15 },
      { label: 'Failed Node', color: '#ef4444', y: 30 },
      { label: 'High Traffic', color: color, y: 45, pulse: true }
    ];
    
    legendItems.forEach(item => {
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('cx', 10);
      circle.setAttribute('cy', item.y);
      circle.setAttribute('r', 4);
      circle.setAttribute('fill', item.color);
      legend.appendChild(circle);
      
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', 20);
      text.setAttribute('y', item.y + 3);
      text.setAttribute('font-size', '10');
      text.setAttribute('fill', '#374151');
      text.textContent = item.label;
      legend.appendChild(text);
    });
    
    svg.appendChild(legend);

  }, [topologyData, networkState, color]);

  if (isLoading) {
    return (
      <div className="network-visualization loading">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ 
              width: '32px', 
              height: '32px', 
              border: '3px solid #e5e7eb', 
              borderTop: '3px solid #3b82f6', 
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite',
              margin: '0 auto 0.5rem'
            }}></div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>Loading network...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="network-visualization">
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100%',
          background: '#fef2f2',
          color: '#dc2626',
          borderRadius: '4px',
          padding: '1rem',
          textAlign: 'center'
        }}>
          <div>
            <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>⚠️</div>
            <div style={{ fontSize: '0.875rem' }}>{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="network-visualization">
      <svg 
        ref={svgRef}
        style={{ 
          width: '100%', 
          height: '100%', 
          border: '1px solid #e5e7eb', 
          borderRadius: '4px',
          background: '#fafafa'
        }}
      >
        {/* SVG content will be added by useEffect */}
      </svg>
      
      {/* Network Status Overlay */}
      <div style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        background: 'rgba(255,255,255,0.9)',
        padding: '0.5rem',
        borderRadius: '4px',
        fontSize: '0.75rem',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
          {simulationState === 'running' ? '🟢 Live' : '⚫ Offline'}
        </div>
        {networkState && (
          <div style={{ color: '#6b7280' }}>
            Last update: {new Date(networkState.timestamp * 1000).toLocaleTimeString()}
          </div>
        )}
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

export default NetworkVisualization;