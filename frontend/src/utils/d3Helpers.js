/**
 * D3.js helper functions for network visualization.
 * Provides utilities for creating interactive network diagrams.
 */

// D3 helpers for network visualization (placeholder for future D3 integration)
export const d3Helpers = {
  /**
   * Create force simulation for network layout
   */
  createForceSimulation: (nodes, links, width, height) => {
    // This would use D3's force simulation
    // For now, return a simple layout
    return {
      nodes: nodes.map((node, i) => ({
        ...node,
        x: node.x || (width / 2) + (Math.cos(i * 2 * Math.PI / nodes.length) * 100),
        y: node.y || (height / 2) + (Math.sin(i * 2 * Math.PI / nodes.length) * 100)
      })),
      links: links
    };
  },

  /**
   * Calculate link path for curved edges
   */
  calculateLinkPath: (source, target, curvature = 0.3) => {
    const dx = target.x - source.x;
    const dy = target.y - source.y;
    const dr = Math.sqrt(dx * dx + dy * dy) * curvature;
    
    return `M${source.x},${source.y}A${dr},${dr} 0 0,1 ${target.x},${target.y}`;
  },

  /**
   * Generate color scale for network metrics
   */
  getColorScale: (domain, range) => {
    // Simple linear interpolation
    return (value) => {
      const ratio = (value - domain[0]) / (domain[1] - domain[0]);
      const clampedRatio = Math.max(0, Math.min(1, ratio));
      
      // Simple interpolation between two colors
      if (range.length === 2) {
        const [color1, color2] = range;
        return interpolateColor(color1, color2, clampedRatio);
      }
      
      return range[0];
    };
  },

  /**
   * Create interactive tooltips
   */
  createTooltip: (content) => {
    return {
      show: (x, y) => {
        // Implementation would create and position tooltip
        console.log(`Tooltip at (${x}, ${y}): ${content}`);
      },
      hide: () => {
        // Implementation would hide tooltip
        console.log('Hide tooltip');
      }
    };
  },

  /**
   * Animate network changes
   */
  animateTransition: (selection, duration = 300) => {
    // Implementation would use D3 transitions
    return {
      duration: duration,
      ease: 'ease-in-out'
    };
  },

  /**
   * Handle zoom and pan
   */
  setupZoomPan: (svg, container) => {
    // Implementation would set up D3 zoom behavior
    return {
      scale: 1,
      translate: [0, 0]
    };
  }
};

// Helper function to interpolate between two colors
function interpolateColor(color1, color2, ratio) {
  // Simple RGB interpolation
  const hex2rgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : null;
  };

  const rgb2hex = (r, g, b) => {
    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  };

  const c1 = hex2rgb(color1);
  const c2 = hex2rgb(color2);
  
  if (!c1 || !c2) return color1;

  const r = Math.round(c1.r + (c2.r - c1.r) * ratio);
  const g = Math.round(c1.g + (c2.g - c1.g) * ratio);
  const b = Math.round(c1.b + (c2.b - c1.b) * ratio);

  return rgb2hex(r, g, b);
}

export default d3Helpers;