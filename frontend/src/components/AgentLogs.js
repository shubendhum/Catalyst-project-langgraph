import React, { useEffect, useRef } from 'react';
import { useProjectStore } from '../store/useProjectStore';

const AgentLogs = ({ taskId }) => {
  const { logs, fetchLogs } = useProjectStore();
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (taskId) {
      fetchLogs(taskId);
    }
  }, [taskId]);

  useEffect(() => {
    // Auto-scroll to bottom
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const getLogColor = (agentName) => {
    const colors = {
      Planner: '#9f7aea',
      Architect: '#ed8936',
      Coder: '#4299e1',
      Tester: '#48bb78',
      Reviewer: '#ecc94b',
      Deployer: '#f56565',
      Explorer: '#38b2ac',
    };
    return colors[agentName] || '#63b3ed';
  };

  return (
    <div
      data-testid="agent-logs"
      style={{
        maxHeight: '400px',
        overflowY: 'auto',
        padding: '16px',
        background: 'rgba(0, 0, 0, 0.3)',
        borderRadius: '12px',
        fontFamily: 'monospace',
      }}
    >
      {logs.length === 0 ? (
        <p style={{ color: '#718096', textAlign: 'center', padding: '24px' }}>No logs yet...</p>
      ) : (
        logs.map((log, index) => (
          <div
            key={index}
            data-testid={`log-entry-${index}`}
            style={{
              marginBottom: '12px',
              padding: '12px',
              background: 'rgba(255, 255, 255, 0.02)',
              borderLeft: `3px solid ${getLogColor(log.agent_name)}`,
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
              <span style={{ fontWeight: '600', color: getLogColor(log.agent_name), fontSize: '13px' }}>
                {log.agent_name}
              </span>
              <span style={{ fontSize: '11px', color: '#718096' }}>
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p style={{ fontSize: '13px', color: '#e4e8f0', lineHeight: '1.5' }}>{log.message}</p>
          </div>
        ))
      )}
      <div ref={logsEndRef} />
    </div>
  );
};

export default AgentLogs;