import React from 'react';
import { CheckCircle2, Circle, XCircle, RefreshCw } from 'lucide-react';

const agents = [
  { id: 'planner', name: 'Planner', emoji: '🧠' },
  { id: 'architect', name: 'Architect', emoji: '🏗️' },
  { id: 'coder', name: 'Coder', emoji: '💻' },
  { id: 'tester', name: 'Tester', emoji: '🧪' },
  { id: 'reviewer', name: 'Reviewer', emoji: '👀' },
  { id: 'deployer', name: 'Deployer', emoji: '🚀' },
];

const TaskGraph = ({ graphState, status }) => {
  const getNodeStatus = (agentId) => {
    if (!graphState || !graphState[agentId]) return 'pending';
    return graphState[agentId];
  };

  const getNodeIcon = (nodeStatus) => {
    switch (nodeStatus) {
      case 'completed':
        return <CheckCircle2 size={20} style={{ color: '#68d391' }} />;
      case 'reworking':
        return <RefreshCw size={20} style={{ color: '#ed8936' }} className="animate-spin" />;
      case 'failed':
        return <XCircle size={20} style={{ color: '#fc8181' }} />;
      default:
        return <Circle size={20} style={{ color: '#4a5568' }} />;
    }
  };

  return (
    <div data-testid="task-graph" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
        {agents.map((agent, index) => {
          const nodeStatus = getNodeStatus(agent.id);
          const isActive = nodeStatus !== 'pending';

          return (
            <React.Fragment key={agent.id}>
              <div
                data-testid={`agent-node-${agent.id}`}
                style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '16px',
                  background: isActive ? 'rgba(99, 179, 237, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                  border: isActive ? '2px solid rgba(99, 179, 237, 0.3)' : '2px solid rgba(255, 255, 255, 0.05)',
                  borderRadius: '16px',
                  transition: 'all 0.3s',
                }}
              >
                <div
                  style={{
                    width: '64px',
                    height: '64px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: isActive ? 'rgba(99, 179, 237, 0.2)' : 'rgba(255, 255, 255, 0.03)',
                    borderRadius: '50%',
                    fontSize: '32px',
                    transition: 'all 0.3s',
                  }}
                >
                  {agent.emoji}
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '4px' }}>{agent.name}</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                    {getNodeIcon(nodeStatus)}
                    <span style={{ fontSize: '12px', color: '#a0aec0', textTransform: 'capitalize' }}>{nodeStatus}</span>
                  </div>
                </div>
              </div>

              {index < agents.length - 1 && (
                <div
                  style={{
                    width: '40px',
                    height: '2px',
                    background:
                      getNodeStatus(agents[index + 1].id) !== 'pending'
                        ? 'linear-gradient(90deg, rgba(99, 179, 237, 0.5), rgba(99, 179, 237, 0.5))'
                        : 'rgba(255, 255, 255, 0.1)',
                    transition: 'all 0.3s',
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default TaskGraph;