import React, { useState, useEffect } from 'react';
import './RunsTimelinePanel.css';

interface Run {
  id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  agent: string;
  startTime: string;
  endTime?: string;
  duration?: number;
  cost?: number;
}

interface RunsTimelinePanelProps {
  maxRuns?: number;
  refreshInterval?: number;
}

const RunsTimelinePanel: React.FC<RunsTimelinePanelProps> = ({
  maxRuns = 10,
  refreshInterval = 5000
}) => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRuns();
    
    const interval = setInterval(fetchRuns, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchRuns = async () => {
    try {
      // Mock API call - replace with actual endpoint
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/runs?limit=${maxRuns}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch runs');
      }
      
      const data = await response.json();
      setRuns(data.runs || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch runs:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch runs');
      
      // Use mock data for demo
      setRuns([
        {
          id: 'run-001',
          status: 'completed',
          agent: 'planner',
          startTime: new Date(Date.now() - 3600000).toISOString(),
          endTime: new Date(Date.now() - 3300000).toISOString(),
          duration: 300000,
          cost: 0.0123
        },
        {
          id: 'run-002',
          status: 'completed',
          agent: 'coder',
          startTime: new Date(Date.now() - 3000000).toISOString(),
          endTime: new Date(Date.now() - 2400000).toISOString(),
          duration: 600000,
          cost: 0.0456
        },
        {
          id: 'run-003',
          status: 'failed',
          agent: 'tester',
          startTime: new Date(Date.now() - 1800000).toISOString(),
          endTime: new Date(Date.now() - 1500000).toISOString(),
          duration: 300000,
          cost: 0.0089
        },
        {
          id: 'run-004',
          status: 'running',
          agent: 'reviewer',
          startTime: new Date(Date.now() - 60000).toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return '#3b82f6';
      case 'completed': return '#10b981';
      case 'failed': return '#ef4444';
      case 'cancelled': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return '⟳';
      case 'completed': return '✓';
      case 'failed': return '✗';
      case 'cancelled': return '⊘';
      default: return '?';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const formatTimeAgo = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const handleViewLogs = (runId: string) => {
    // Navigate to logs page with run filter
    window.location.href = `/logs?run=${runId}`;
  };

  if (loading) {
    return (
      <div className="runs-timeline-panel loading">
        <div className="loading-spinner">⟳</div>
        Loading runs...
      </div>
    );
  }

  return (
    <div className="runs-timeline-panel">
      <div className="timeline-header">
        <h3>📊 Recent Runs</h3>
        <button className="refresh-button" onClick={fetchRuns} title="Refresh">
          ↻
        </button>
      </div>

      {error && !runs.length && (
        <div className="timeline-error">
          Failed to load runs. Using demo data.
        </div>
      )}

      <div className="timeline-list">
        {runs.map((run) => (
          <div key={run.id} className="timeline-item">
            <div className="timeline-marker" style={{ backgroundColor: getStatusColor(run.status) }}>
              <span className="marker-icon">{getStatusIcon(run.status)}</span>
            </div>
            
            <div className="timeline-content">
              <div className="timeline-title">
                <span className="run-agent">{run.agent}</span>
                <span className="run-id">#{run.id.slice(0, 8)}</span>
              </div>
              
              <div className="timeline-meta">
                <span className="timeline-time">{formatTimeAgo(run.startTime)}</span>
                {run.duration && (
                  <>
                    <span className="meta-separator">•</span>
                    <span>{formatDuration(run.duration)}</span>
                  </>
                )}
                {run.cost !== undefined && (
                  <>
                    <span className="meta-separator">•</span>
                    <span>${run.cost.toFixed(4)}</span>
                  </>
                )}
              </div>
              
              <button
                className="view-logs-button"
                onClick={() => handleViewLogs(run.id)}
              >
                View Logs →
              </button>
            </div>
          </div>
        ))}
      </div>

      {runs.length === 0 && (
        <div className="timeline-empty">
          No runs yet. Start a task to see activity here.
        </div>
      )}
    </div>
  );
};

export default RunsTimelinePanel;
