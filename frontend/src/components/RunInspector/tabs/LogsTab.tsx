import React, { useState, useMemo } from 'react';
import { RunLog } from '../../../contexts/RunContext';

interface LogsTabProps {
  run: {
    logs: RunLog[];
  };
}

const LogsTab: React.FC<LogsTabProps> = ({ run }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [agentFilter, setAgentFilter] = useState<string>('all');
  const [expandedLog, setExpandedLog] = useState<string | null>(null);

  // Get unique agents
  const agents = useMemo(() => {
    const uniqueAgents = new Set(run.logs.map(log => log.agent).filter(Boolean));
    return Array.from(uniqueAgents);
  }, [run.logs]);

  // Filter logs
  const filteredLogs = useMemo(() => {
    return run.logs.filter(log => {
      // Search filter
      if (searchTerm && !log.message.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      
      // Level filter
      if (levelFilter !== 'all' && log.level !== levelFilter) {
        return false;
      }
      
      // Agent filter
      if (agentFilter !== 'all' && log.agent !== agentFilter) {
        return false;
      }
      
      return true;
    });
  }, [run.logs, searchTerm, levelFilter, agentFilter]);

  if (run.logs.length === 0) {
    return (
      <div className="logs-tab p-6">
        <div className="text-center py-12 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-2 text-sm">No logs available yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="logs-tab p-6 space-y-4">
      {/* Filters */}
      <div className="filters bg-white border border-gray-200 rounded-lg p-4">
        <div className="grid grid-cols-3 gap-4">
          {/* Search */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Search</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search logs..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Level Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Level</label>
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARN">Warning</option>
              <option value="ERROR">Error</option>
            </select>
          </div>
          
          {/* Agent Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Agent</label>
            <select
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Agents</option>
              {agents.map(agent => (
                <option key={agent} value={agent}>{agent}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="mt-3 text-xs text-gray-500">
          Showing {filteredLogs.length} of {run.logs.length} logs
        </div>
      </div>

      {/* Logs List */}
      <div className="logs-list space-y-2">
        {filteredLogs.map((log) => (
          <div key={log.id} className="log-entry bg-white border border-gray-200 rounded-lg">
            <div
              className="log-header p-3 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
            >
              <div className="flex items-start gap-3">
                <LogLevelBadge level={log.level} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleTimeString()}</p>
                    {log.agent && (
                      <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                        {log.agent}
                      </span>
                    )}
                    {log.tool && (
                      <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-800 rounded">
                        {log.tool}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-900 mt-1">{log.message}</p>
                </div>
                {log.details && (
                  <svg
                    className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${
                      expandedLog === log.id ? 'transform rotate-180' : ''
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </div>
            </div>
            
            {expandedLog === log.id && log.details && (
              <div className="log-details p-3 border-t border-gray-200 bg-gray-50">
                <pre className="text-xs text-gray-700 overflow-x-auto">
                  {JSON.stringify(log.details, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
        
        {filteredLogs.length === 0 && (
          <div className="text-center py-8 text-gray-500 text-sm">
            <p>No logs match your filters</p>
          </div>
        )}
      </div>
    </div>
  );
};

function LogLevelBadge({ level }: { level: string }) {
  const classes: Record<string, string> = {
    'DEBUG': 'bg-gray-100 text-gray-800',
    'INFO': 'bg-blue-100 text-blue-800',
    'WARN': 'bg-yellow-100 text-yellow-800',
    'ERROR': 'bg-red-100 text-red-800',
  };
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium flex-shrink-0 ${classes[level] || classes.INFO}`}>
      {level}
    </span>
  );
}

export default LogsTab;