import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/useProjectStore';
import { ArrowLeft, Play, Activity, Code, CheckCircle2, XCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import TaskGraph from '../components/TaskGraph';
import AgentLogs from '../components/AgentLogs';
import CreditMeter from '../components/CreditMeter';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ProjectView = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentProject, fetchProject, tasks, fetchTasks, createTask, fetchLogs, addLog, updateTaskStatus } = useProjectStore();
  const [prompt, setPrompt] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [activeTask, setActiveTask] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (id) {
      fetchProject(id);
      fetchTasks(id);
    }
  }, [id]);

  useEffect(() => {
    // Connect to WebSocket if there's an active task
    if (activeTask && activeTask.status === 'running') {
      connectWebSocket(activeTask.id);
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [activeTask]);

  const connectWebSocket = (taskId) => {
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    wsRef.current = new WebSocket(`${wsUrl}/ws/${taskId}`);

    wsRef.current.onmessage = (event) => {
      const log = JSON.parse(event.data);
      addLog(log);
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  };

  const handleRunTask = async () => {
    if (prompt.trim() && !isRunning) {
      setIsRunning(true);
      const task = await createTask(id, prompt);
      if (task) {
        setActiveTask(task);
        fetchLogs(task.id);
        // Poll for task updates
        const interval = setInterval(async () => {
          await fetchTasks(id);
          const updatedTask = tasks.find(t => t.id === task.id);
          if (updatedTask) {
            setActiveTask(updatedTask);
            if (updatedTask.status === 'completed' || updatedTask.status === 'failed') {
              clearInterval(interval);
              setIsRunning(false);
            }
          }
        }, 2000);
      } else {
        setIsRunning(false);
      }
    }
  };

  if (!currentProject) {
    return <div style={{ padding: '48px', textAlign: 'center' }}>Loading...</div>;
  }

  return (
    <div data-testid="project-view-page" style={{ minHeight: '100vh', padding: '24px' }}>
      <div style={{ maxWidth: '1600px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button data-testid="back-to-dashboard-btn" onClick={() => navigate('/')} className="btn-secondary" style={{ padding: '8px' }}>
              <ArrowLeft size={20} />
            </Button>
            <div>
              <h1 data-testid="project-name" style={{ fontSize: '32px', fontWeight: '700', marginBottom: '4px' }}>{currentProject.name}</h1>
              <p style={{ color: '#a0aec0' }}>{currentProject.description}</p>
            </div>
          </div>
          <CreditMeter cost={activeTask?.cost || 0} />
        </div>

        {/* Main Content */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
          {/* Left: Chat Input */}
          <div className="glass" style={{ padding: '24px', height: 'fit-content' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <Activity size={24} style={{ color: '#63b3ed' }} />
              <h2 style={{ fontSize: '20px', fontWeight: '600' }}>AI Agent Orchestrator</h2>
            </div>
            <p style={{ color: '#a0aec0', fontSize: '14px', marginBottom: '20px' }}>
              Describe what you want to build, and Catalyst's multi-agent system will plan, code, test, and deploy it.
            </p>
            <Textarea
              data-testid="task-prompt-input"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Build a task management app with React frontend and FastAPI backend..."
              rows={6}
              style={{ width: '100%', marginBottom: '16px' }}
              disabled={isRunning}
            />
            <Button
              data-testid="run-task-btn"
              onClick={handleRunTask}
              className="btn-primary"
              disabled={isRunning || !prompt.trim()}
              style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              <Play size={20} />
              {isRunning ? 'Running...' : 'Run Task'}
            </Button>
          </div>

          {/* Right: Task Status */}
          {activeTask && (
            <div className="glass" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Task Status</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                <span className={`status-badge status-${activeTask.status}`}>{activeTask.status}</span>
                {activeTask.status === 'completed' && <CheckCircle2 size={20} style={{ color: '#68d391' }} />}
                {activeTask.status === 'failed' && <XCircle size={20} style={{ color: '#fc8181' }} />}
              </div>
              <div style={{ padding: '16px', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '12px', marginBottom: '16px' }}>
                <p style={{ fontSize: '14px', color: '#e4e8f0' }}>{activeTask.prompt}</p>
              </div>
              {activeTask.cost > 0 && (
                <div style={{ fontSize: '14px', color: '#a0aec0' }}>
                  <strong>Cost:</strong> ${activeTask.cost.toFixed(2)}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Task Graph */}
        {activeTask && (
          <div className="glass" style={{ padding: '24px', marginBottom: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Agent Execution Graph</h3>
            <TaskGraph graphState={activeTask.graph_state || {}} status={activeTask.status} />
          </div>
        )}

        {/* Agent Logs */}
        {activeTask && (
          <div className="glass" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Agent Logs</h3>
            <AgentLogs taskId={activeTask.id} />
          </div>
        )}

        {/* Previous Tasks */}
        {tasks.length > 0 && (
          <div className="glass" style={{ padding: '24px', marginTop: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Task History</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {tasks.map((task) => (
                <div
                  key={task.id}
                  data-testid={`task-history-item-${task.id}`}
                  onClick={() => {
                    setActiveTask(task);
                    fetchLogs(task.id);
                  }}
                  style={{
                    padding: '16px',
                    background: activeTask?.id === task.id ? 'rgba(99, 179, 237, 0.1)' : 'rgba(0, 0, 0, 0.2)',
                    borderRadius: '12px',
                    cursor: 'pointer',
                    border: activeTask?.id === task.id ? '1px solid rgba(99, 179, 237, 0.3)' : '1px solid transparent',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ flex: 1 }}>
                      <p style={{ fontSize: '14px', marginBottom: '4px' }}>{task.prompt}</p>
                      <p style={{ fontSize: '12px', color: '#718096' }}>
                        {new Date(task.created_at).toLocaleString()}
                      </p>
                    </div>
                    <span className={`status-badge status-${task.status}`}>{task.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectView;