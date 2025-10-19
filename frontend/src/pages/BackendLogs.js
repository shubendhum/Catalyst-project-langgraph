import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertCircle, Info, CheckCircle, Clock, Home, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const BackendLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState(5); // minutes
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [filterSource, setFilterSource] = useState('all');

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/logs/backend?minutes=${timeframe}`);
      const data = await response.json();
      
      if (data.success) {
        setLogs(data.logs);
      } else {
        setError(data.error || 'Failed to fetch logs');
      }
    } catch (err) {
      setError('Failed to connect to backend: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [timeframe]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, 10000); // Refresh every 10 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh, timeframe]);

  const getLogIcon = (log) => {
    const message = log.message.toLowerCase();
    if (message.includes('error') || message.includes('failed')) {
      return <AlertCircle className="w-4 h-4 text-red-500" />;
    } else if (message.includes('warning')) {
      return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    } else if (message.includes('success') || message.includes('✅') || message.includes('✓')) {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
    return <Info className="w-4 h-4 text-blue-500" />;
  };

  const getLogClass = (log) => {
    const message = log.message.toLowerCase();
    if (message.includes('error') || message.includes('failed')) {
      return 'bg-red-50 border-red-200';
    } else if (message.includes('warning')) {
      return 'bg-yellow-50 border-yellow-200';
    } else if (message.includes('success') || message.includes('✅')) {
      return 'bg-green-50 border-green-200';
    }
    return 'bg-white border-gray-200';
  };

  const filteredLogs = filterSource === 'all' 
    ? logs 
    : logs.filter(log => log.source === filterSource || (filterSource === 'agent' && log.source === 'agent'));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Backend Logs</h1>
          <p className="text-gray-600">View real-time backend logs and agent activity</p>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap items-center gap-4">
            {/* Timeframe selector */}
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-700">Last:</span>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(Number(e.target.value))}
                className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>1 minute</option>
                <option value={5}>5 minutes</option>
                <option value={15}>15 minutes</option>
                <option value={30}>30 minutes</option>
                <option value={60}>1 hour</option>
              </select>
            </div>

            {/* Source filter */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700">Source:</span>
              <select
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                className="border border-gray-300 rounded px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="agent">Agents</option>
                <option value="backend.out.log">Backend Output</option>
                <option value="backend.err.log">Backend Errors</option>
              </select>
            </div>

            {/* Auto-refresh toggle */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Auto-refresh (10s)</span>
            </label>

            {/* Refresh button */}
            <button
              onClick={fetchLogs}
              disabled={loading}
              className="ml-auto flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-900">Error Loading Logs</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Logs display */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Logs ({filteredLogs.length})
            </h2>
            {loading && (
              <span className="text-sm text-gray-500">Loading...</span>
            )}
          </div>

          <div className="divide-y divide-gray-200 max-h-[70vh] overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Info className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <p>No logs found for the selected timeframe</p>
              </div>
            ) : (
              filteredLogs.map((log, index) => (
                <div
                  key={index}
                  className={`p-4 hover:bg-gray-50 transition-colors ${getLogClass(log)} border-l-4`}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                      {getLogIcon(log)}
                    </div>
                    <div className="flex-grow min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-medium text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
                            {log.source}
                          </span>
                          {log.agent_name && (
                            <span className="text-xs font-medium text-blue-600 bg-blue-100 px-2 py-0.5 rounded">
                              {log.agent_name}
                            </span>
                          )}
                          {log.task_id && (
                            <span className="text-xs font-mono text-gray-500">
                              Task: {log.task_id.substring(0, 8)}...
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-gray-500 flex-shrink-0">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 font-mono break-words whitespace-pre-wrap">
                        {log.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackendLogs;
