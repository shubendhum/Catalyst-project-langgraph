import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

// Types
export interface RunMetadata {
  runId: string;
  taskId?: string;
  name: string;
  description?: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';
  startTime?: string;
  endTime?: string;
  duration?: number;
  cost?: number;
  tokens?: number;
  inputMessage?: string;
}

export interface RunEvent {
  id: string;
  timestamp: string;
  type: 'agent_started' | 'agent_finished' | 'tool_call' | 'file_operation' | 'test_run' | 'error' | 'thinking';
  agent?: string;
  tool?: string;
  description: string;
  details?: any;
}

export interface RunFile {
  path: string;
  operation: 'create' | 'modify' | 'delete';
  timestamp: string;
  content?: string;
  previousContent?: string;
  size?: number;
}

export interface RunTest {
  id: string;
  command: string;
  status: 'not_run' | 'running' | 'passed' | 'failed';
  exitCode?: number;
  stdout?: string;
  stderr?: string;
  duration?: number;
  timestamp?: string;
  summary?: {
    total: number;
    passed: number;
    failed: number;
  };
}

export interface RunLog {
  id: string;
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  agent?: string;
  tool?: string;
  details?: any;
}

export interface RunStage {
  name: string;
  status: 'not_started' | 'running' | 'success' | 'failed';
  agent?: string;
  startTime?: string;
  endTime?: string;
}

interface RunData {
  metadata: RunMetadata;
  events: RunEvent[];
  files: RunFile[];
  tests: RunTest[];
  logs: RunLog[];
  stages: RunStage[];
}

interface RunContextType {
  // Selected run
  selectedRunId: string | null;
  selectRun: (runId: string) => void;
  
  // Run data
  runs: Map<string, RunData>;
  getCurrentRun: () => RunData | null;
  
  // Update methods
  updateRunMetadata: (runId: string, metadata: Partial<RunMetadata>) => void;
  addRunEvent: (runId: string, event: RunEvent) => void;
  addRunFile: (runId: string, file: RunFile) => void;
  updateRunTest: (runId: string, test: RunTest) => void;
  addRunLog: (runId: string, log: RunLog) => void;
  updateRunStage: (runId: string, stageName: string, update: Partial<RunStage>) => void;
  
  // Initialization
  initializeRun: (runId: string, metadata: RunMetadata) => void;
  clearRun: (runId: string) => void;
}

const RunContext = createContext<RunContextType | undefined>(undefined);

export const RunProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [runs, setRuns] = useState<Map<string, RunData>>(new Map());

  // Initialize a new run
  const initializeRun = useCallback((runId: string, metadata: RunMetadata) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      
      // Initialize with default stages
      const defaultStages: RunStage[] = [
        { name: 'Planning', status: 'not_started', agent: 'planner' },
        { name: 'Architecture', status: 'not_started', agent: 'architect' },
        { name: 'Implementation', status: 'not_started', agent: 'coder' },
        { name: 'Testing', status: 'not_started', agent: 'tester' },
        { name: 'Review', status: 'not_started', agent: 'reviewer' },
        { name: 'Deployment', status: 'not_started', agent: 'deployer' },
      ];
      
      newRuns.set(runId, {
        metadata,
        events: [],
        files: [],
        tests: [],
        logs: [],
        stages: defaultStages,
      });
      
      return newRuns;
    });
  }, []);

  // Select a run
  const selectRun = useCallback((runId: string) => {
    setSelectedRunId(runId);
    
    // Initialize if doesn't exist
    setRuns(prev => {
      if (!prev.has(runId)) {
        const newRuns = new Map(prev);
        const defaultStages: RunStage[] = [
          { name: 'Planning', status: 'not_started', agent: 'planner' },
          { name: 'Architecture', status: 'not_started', agent: 'architect' },
          { name: 'Implementation', status: 'not_started', agent: 'coder' },
          { name: 'Testing', status: 'not_started', agent: 'tester' },
          { name: 'Review', status: 'not_started', agent: 'reviewer' },
          { name: 'Deployment', status: 'not_started', agent: 'deployer' },
        ];
        
        newRuns.set(runId, {
          metadata: {
            runId,
            name: `Run ${runId.substring(0, 8)}`,
            status: 'running',
          },
          events: [],
          files: [],
          tests: [],
          logs: [],
          stages: defaultStages,
        });
        return newRuns;
      }
      return prev;
    });
  }, []);

  // Get current run data
  const getCurrentRun = useCallback((): RunData | null => {
    if (!selectedRunId) return null;
    return runs.get(selectedRunId) || null;
  }, [selectedRunId, runs]);

  // Update run metadata
  const updateRunMetadata = useCallback((runId: string, metadata: Partial<RunMetadata>) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        run.metadata = { ...run.metadata, ...metadata };
        newRuns.set(runId, run);
      }
      return newRuns;
    });
  }, []);

  // Add event
  const addRunEvent = useCallback((runId: string, event: RunEvent) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        run.events.push(event);
        newRuns.set(runId, run);
      }
      return newRuns;
    });
  }, []);

  // Add file
  const addRunFile = useCallback((runId: string, file: RunFile) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        // Update or add file
        const existingIndex = run.files.findIndex(f => f.path === file.path);
        if (existingIndex >= 0) {
          run.files[existingIndex] = file;
        } else {
          run.files.push(file);
        }
        newRuns.set(runId, run);
      }
      return newRuns;
    });
  }, []);

  // Update test
  const updateRunTest = useCallback((runId: string, test: RunTest) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        const existingIndex = run.tests.findIndex(t => t.id === test.id);
        if (existingIndex >= 0) {
          run.tests[existingIndex] = test;
        } else {
          run.tests.push(test);
        }
        newRuns.set(runId, run);
      }
      return newRuns;
    });
  }, []);

  // Add log
  const addRunLog = useCallback((runId: string, log: RunLog) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        run.logs.push(log);
        // Keep only last 1000 logs to avoid memory issues
        if (run.logs.length > 1000) {
          run.logs = run.logs.slice(-1000);
        }
        newRuns.set(runId, run);
      }
      return newRuns;
    });
  }, []);

  // Update stage
  const updateRunStage = useCallback((runId: string, stageName: string, update: Partial<RunStage>) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      const run = newRuns.get(runId);
      if (run) {
        const stageIndex = run.stages.findIndex(s => s.name === stageName);
        if (stageIndex >= 0) {
          run.stages[stageIndex] = { ...run.stages[stageIndex], ...update };
          newRuns.set(runId, run);
        }
      }
      return newRuns;
    });
  }, []);

  // Clear run
  const clearRun = useCallback((runId: string) => {
    setRuns(prev => {
      const newRuns = new Map(prev);
      newRuns.delete(runId);
      return newRuns;
    });
    
    if (selectedRunId === runId) {
      setSelectedRunId(null);
    }
  }, [selectedRunId]);

  const value: RunContextType = {
    selectedRunId,
    selectRun,
    runs,
    getCurrentRun,
    updateRunMetadata,
    addRunEvent,
    addRunFile,
    updateRunTest,
    addRunLog,
    updateRunStage,
    initializeRun,
    clearRun,
  };

  return <RunContext.Provider value={value}>{children}</RunContext.Provider>;
};

export const useRun = () => {
  const context = useContext(RunContext);
  if (!context) {
    throw new Error('useRun must be used within a RunProvider');
  }
  return context;
};
