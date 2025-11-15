import React from 'react';
import './AgentRunCard.css';

interface Artifact {
  name: string;
  type: string;
  path: string;
  size?: string;
}

interface TestResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
}

interface AgentRunCardProps {
  runId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  agent: string;
  plan?: string;
  artifacts?: Artifact[];
  testResults?: TestResult[];
  cost?: number;
  duration?: number;
  startTime: string;
  endTime?: string;
}

const AgentRunCard: React.FC<AgentRunCardProps> = ({
  runId,
  status,
  agent,
  plan,
  artifacts = [],
  testResults = [],
  cost,
  duration,
  startTime,
  endTime
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'running': return '#3b82f6';
      case 'completed': return '#10b981';
      case 'failed': return '#ef4444';
      case 'cancelled': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = () => {
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
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  const formatCost = (cost?: number) => {
    if (cost === undefined || cost === null) return 'N/A';
    return `$${cost.toFixed(4)}`;
  };

  const testsPassed = testResults.filter(t => t.status === 'passed').length;
  const testsFailed = testResults.filter(t => t.status === 'failed').length;
  const testsTotal = testResults.length;

  return (
    <div className="agent-run-card">
      <div className="run-header">
        <div className="run-status" style={{ backgroundColor: getStatusColor() }}>
          <span className="status-icon">{getStatusIcon()}</span>
          <span className="status-text">{status.toUpperCase()}</span>
        </div>
        <div className="run-meta">
          <span className="run-id">#{runId.slice(0, 8)}</span>
          <span className="run-agent">{agent}</span>
        </div>
      </div>

      {plan && (
        <div className="run-section">
          <h4>📋 Plan</h4>
          <div className="plan-content">
            {plan}
          </div>
        </div>
      )}

      {artifacts.length > 0 && (
        <div className="run-section">
          <h4>📦 Artifacts ({artifacts.length})</h4>
          <div className="artifacts-list">
            {artifacts.map((artifact, index) => (
              <div key={index} className="artifact-item">
                <span className="artifact-icon">
                  {artifact.type === 'file' ? '📄' : '📁'}
                </span>
                <span className="artifact-name">{artifact.name}</span>
                <span className="artifact-size">{artifact.size}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {testResults.length > 0 && (
        <div className="run-section">
          <h4>🧪 Tests ({testsPassed}/{testsTotal} passed)</h4>
          <div className="test-results">
            {testResults.map((test, index) => (
              <div key={index} className={`test-item test-${test.status}`}>
                <span className="test-icon">
                  {test.status === 'passed' ? '✓' : test.status === 'failed' ? '✗' : '○'}
                </span>
                <span className="test-name">{test.name}</span>
                <span className="test-duration">{test.duration}ms</span>
                {test.error && (
                  <div className="test-error">{test.error}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="run-footer">
        <div className="run-stat">
          <span className="stat-label">Duration</span>
          <span className="stat-value">{formatDuration(duration)}</span>
        </div>
        <div className="run-stat">
          <span className="stat-label">Cost</span>
          <span className="stat-value">{formatCost(cost)}</span>
        </div>
        <div className="run-stat">
          <span className="stat-label">Started</span>
          <span className="stat-value">{new Date(startTime).toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  );
};

export default AgentRunCard;
