import React, { useState, useEffect } from 'react';
import './Status.css';

interface DependencyStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  message?: string;
  [key: string]: any;
}

interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  dependencies: {
    mongodb: DependencyStatus;
    redis: DependencyStatus;
    qdrant: DependencyStatus;
    model: DependencyStatus;
  };
}

const Status: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/health`);
      const data = await response.json();
      
      // Handle both 200 and 503 responses
      if (response.status === 503 && data.detail) {
        setHealth(data.detail);
      } else {
        setHealth(data);
      }
      
      setError(null);
      setLastRefresh(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health status');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    
    // Poll every 10 seconds
    const interval = setInterval(fetchHealth, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#10b981'; // green
      case 'degraded':
        return '#f59e0b'; // amber
      case 'unhealthy':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return '✓';
      case 'degraded':
        return '⚠';
      case 'unhealthy':
        return '✗';
      default:
        return '?';
    }
  };

  if (loading) {
    return (
      <div className="status-container">
        <div className="status-loading">Loading system status...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="status-container">
        <div className="status-error">
          <h2>Error Loading Status</h2>
          <p>{error}</p>
          <button onClick={fetchHealth}>Retry</button>
        </div>
      </div>
    );
  }

  if (!health) {
    return null;
  }

  return (
    <div className="status-container">
      <div className="status-header">
        <h1>System Status</h1>
        <div className="status-overall" style={{ backgroundColor: getStatusColor(health.status) }}>
          <span className="status-icon">{getStatusIcon(health.status)}</span>
          <span className="status-text">{health.status.toUpperCase()}</span>
        </div>
      </div>

      <div className="status-info">
        <p>Last refreshed: {lastRefresh.toLocaleTimeString()}</p>
        <p>Auto-refresh every 10 seconds</p>
      </div>

      <div className="status-grid">
        {/* MongoDB Card */}
        <div className="status-card">
          <div 
            className="status-card-header" 
            style={{ borderLeftColor: getStatusColor(health.dependencies.mongodb.status) }}
          >
            <span className="status-card-icon">{getStatusIcon(health.dependencies.mongodb.status)}</span>
            <h3>MongoDB</h3>
          </div>
          <div className="status-card-body">
            <div className="status-badge" style={{ backgroundColor: getStatusColor(health.dependencies.mongodb.status) }}>
              {health.dependencies.mongodb.status}
            </div>
            {health.dependencies.mongodb.version && (
              <p className="status-detail">Version: {health.dependencies.mongodb.version}</p>
            )}
            {health.dependencies.mongodb.message && (
              <p className="status-message">{health.dependencies.mongodb.message}</p>
            )}
          </div>
        </div>

        {/* Redis Card */}
        <div className="status-card">
          <div 
            className="status-card-header" 
            style={{ borderLeftColor: getStatusColor(health.dependencies.redis.status) }}
          >
            <span className="status-card-icon">{getStatusIcon(health.dependencies.redis.status)}</span>
            <h3>Redis</h3>
          </div>
          <div className="status-card-body">
            <div className="status-badge" style={{ backgroundColor: getStatusColor(health.dependencies.redis.status) }}>
              {health.dependencies.redis.status}
            </div>
            {health.dependencies.redis.version && (
              <p className="status-detail">Version: {health.dependencies.redis.version}</p>
            )}
            {health.dependencies.redis.connected_clients !== undefined && (
              <p className="status-detail">Clients: {health.dependencies.redis.connected_clients}</p>
            )}
            {health.dependencies.redis.message && (
              <p className="status-message">{health.dependencies.redis.message}</p>
            )}
          </div>
        </div>

        {/* Qdrant Card */}
        <div className="status-card">
          <div 
            className="status-card-header" 
            style={{ borderLeftColor: getStatusColor(health.dependencies.qdrant.status) }}
          >
            <span className="status-card-icon">{getStatusIcon(health.dependencies.qdrant.status)}</span>
            <h3>Qdrant</h3>
          </div>
          <div className="status-card-body">
            <div className="status-badge" style={{ backgroundColor: getStatusColor(health.dependencies.qdrant.status) }}>
              {health.dependencies.qdrant.status}
            </div>
            {health.dependencies.qdrant.collections_count !== undefined && (
              <p className="status-detail">Collections: {health.dependencies.qdrant.collections_count}</p>
            )}
            {health.dependencies.qdrant.message && (
              <p className="status-message">{health.dependencies.qdrant.message}</p>
            )}
          </div>
        </div>

        {/* LLM Model Card */}
        <div className="status-card">
          <div 
            className="status-card-header" 
            style={{ borderLeftColor: getStatusColor(health.dependencies.model.status) }}
          >
            <span className="status-card-icon">{getStatusIcon(health.dependencies.model.status)}</span>
            <h3>LLM Model</h3>
          </div>
          <div className="status-card-body">
            <div className="status-badge" style={{ backgroundColor: getStatusColor(health.dependencies.model.status) }}>
              {health.dependencies.model.status}
            </div>
            {health.dependencies.model.provider && (
              <p className="status-detail">Provider: {health.dependencies.model.provider}</p>
            )}
            {health.dependencies.model.model && (
              <p className="status-detail">Model: {health.dependencies.model.model}</p>
            )}
            {health.dependencies.model.key_configured !== undefined && (
              <p className="status-detail">
                Key: {health.dependencies.model.key_configured ? '✓ Configured' : '✗ Missing'}
              </p>
            )}
            {health.dependencies.model.message && (
              <p className="status-message">{health.dependencies.model.message}</p>
            )}
          </div>
        </div>
      </div>

      <div className="status-footer">
        <button onClick={fetchHealth} className="refresh-button">
          Refresh Now
        </button>
      </div>
    </div>
  );
};

export default Status;
