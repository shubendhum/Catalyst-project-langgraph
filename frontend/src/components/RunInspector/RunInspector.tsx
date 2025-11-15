import React, { useState } from 'react';
import { useRun } from '../../contexts/RunContext';
import OverviewTab from './tabs/OverviewTab';
import FilesTab from './tabs/FilesTab';
import TestsTab from './tabs/TestsTab';
import LogsTab from './tabs/LogsTab';
import EventsTab from './tabs/EventsTab';

type TabType = 'overview' | 'files' | 'tests' | 'logs' | 'events';

const RunInspector: React.FC = () => {
  const { selectedRunId, getCurrentRun } = useRun();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  
  const currentRun = getCurrentRun();

  if (!selectedRunId || !currentRun) {
    return (
      <div className="run-inspector-empty">
        <div className="text-center p-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No run selected</h3>
          <p className="mt-1 text-sm text-gray-500">
            Select a run from the sidebar to view details
          </p>
        </div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string; count?: number }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'files', label: 'Files', count: currentRun.files.length },
    { id: 'tests', label: 'Tests', count: currentRun.tests.length },
    { id: 'logs', label: 'Logs', count: currentRun.logs.length },
    { id: 'events', label: 'Events', count: currentRun.events.length },
  ];

  return (
    <div className="run-inspector flex flex-col h-full bg-white border-l border-gray-200">
      {/* Header */}
      <div className="inspector-header border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {currentRun.metadata.name}
            </h2>
            <p className="text-sm text-gray-500">
              Run ID: {selectedRunId.substring(0, 8)}...
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`status-badge px-2 py-1 rounded text-xs font-medium ${getStatusClass(currentRun.metadata.status)}`}>
              {currentRun.metadata.status}
            </span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="inspector-tabs border-b border-gray-200">
        <nav className="flex space-x-1 px-4" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                px-3 py-2 text-sm font-medium rounded-t-lg transition-colors
                ${activeTab === tab.id
                  ? 'bg-gray-100 text-gray-900 border-b-2 border-blue-500'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }
              `}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-2 bg-gray-200 text-gray-700 px-2 py-0.5 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="inspector-content flex-1 overflow-y-auto">
        {activeTab === 'overview' && <OverviewTab run={currentRun} />}
        {activeTab === 'files' && <FilesTab run={currentRun} />}
        {activeTab === 'tests' && <TestsTab run={currentRun} />}
        {activeTab === 'logs' && <LogsTab run={currentRun} />}
        {activeTab === 'events' && <EventsTab run={currentRun} />}
      </div>
    </div>
  );
};

function getStatusClass(status: string): string {
  switch (status) {
    case 'succeeded':
      return 'bg-green-100 text-green-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'queued':
      return 'bg-yellow-100 text-yellow-800';
    case 'cancelled':
      return 'bg-gray-100 text-gray-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

export default RunInspector;
