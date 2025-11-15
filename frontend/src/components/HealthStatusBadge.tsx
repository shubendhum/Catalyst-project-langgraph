import React, { useState, useEffect } from 'react';
import './HealthStatusBadge.css';

interface HealthStatusBadgeProps {
  refreshInterval?: number;
  showDetails?: boolean;
}

const HealthStatusBadge: React.FC<HealthStatusBadgeProps> = ({
  refreshInterval = 30000,
  showDetails = false
}) => {
  const [status, setStatus] = useState<'healthy' | 'degraded' | 'unhealthy' | 'unknown'>('unknown');
  const [loading, setLoading] = useState(true);
  const [details, setDetails] = useState<any>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  useEffect(() => {
    fetchHealth();
    
    const interval = setInterval(fetchHealth, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/health`);
      
      // Handle both 200 and 503 responses
      const data = await response.json();
      
      if (response.status === 503 && data.detail) {
        setStatus(data.detail.status || 'unhealthy');
        setDetails(data.detail);
      } else {
        setStatus(data.status || 'unknown');
        setDetails(data);
      }
    } catch (error) {
      console.error('Failed to fetch health:', error);
      setStatus('unknown');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'degraded': return '#f59e0b';
      case 'unhealthy': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy': return '●';
      case 'degraded': return '◐';
      case 'unhealthy': return '●';
      default: return '○';
    }
  };

  const getStatusText = () => {
    if (loading) return 'Checking...';
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const handleClick = () => {
    window.location.href = '/status';
  };

  return (
    <div
      className="health-status-badge"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={handleClick}
    >
      <span
        className="status-indicator"
        style={{ color: getStatusColor() }}
      >
        {getStatusIcon()}
      </span>
      <span className="status-text">{getStatusText()}</span>
      
      {showTooltip && details && (
        <div className="status-tooltip">
          <div className="tooltip-header">System Health</div>
          <div className="tooltip-body">
            {details.dependencies && Object.entries(details.dependencies).map(([key, dep]: [string, any]) => (
              <div key={key} className="tooltip-item">
                <span className="tooltip-service">{key}</span>
                <span
                  className="tooltip-status"
                  style={{
                    color: dep.status === 'healthy' ? '#10b981' :
                           dep.status === 'degraded' ? '#f59e0b' :
                           dep.status === 'unhealthy' ? '#ef4444' : '#6b7280'
                  }}
                >
                  {dep.status}
                </span>
              </div>
            ))}
          </div>
          <div className="tooltip-footer">Click for details →</div>
        </div>
      )}
    </div>
  );
};

export default HealthStatusBadge;
