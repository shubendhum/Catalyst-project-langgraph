import React, { useState } from 'react';
import { RunEvent } from '../../../contexts/RunContext';

interface EventsTabProps {
  run: {
    events: RunEvent[];
  };
}

const EventsTab: React.FC<EventsTabProps> = ({ run }) => {
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const eventTypes = ['all', 'agent_started', 'agent_finished', 'tool_call', 'file_operation', 'test_run', 'error', 'thinking'];

  const filteredEvents = run.events.filter(event => {
    if (typeFilter === 'all') return true;
    return event.type === typeFilter;
  });

  if (run.events.length === 0) {
    return (
      <div className="events-tab p-6">
        <div className="text-center py-12 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="mt-2 text-sm">No events recorded yet</p>
        </div>
      </div>
    );
  }

  return (
    <div className="events-tab p-6 space-y-4">
      {/* Filter */}
      <div className="filter bg-white border border-gray-200 rounded-lg p-4">
        <label className="block text-xs font-medium text-gray-700 mb-2">Event Type</label>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {eventTypes.map(type => (
            <option key={type} value={type}>
              {type === 'all' ? 'All Types' : type.replace('_', ' ')}
            </option>
          ))}
        </select>
        <p className="mt-2 text-xs text-gray-500">
          Showing {filteredEvents.length} of {run.events.length} events
        </p>
      </div>

      {/* Timeline */}
      <div className="timeline space-y-4">
        {filteredEvents.map((event, index) => (
          <div key={event.id} className="timeline-item relative">
            {/* Timeline line */}
            {index < filteredEvents.length - 1 && (
              <div className="absolute left-4 top-10 w-0.5 h-full bg-gray-200 -z-10"></div>
            )}
            
            <div className="event-card bg-white border border-gray-200 rounded-lg">
              <div
                className="event-header p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => setExpandedEvent(expandedEvent === event.id ? null : event.id)}
              >
                <div className="flex items-start gap-3">
                  <EventIcon type={event.type} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </p>
                      <EventTypeBadge type={event.type} />
                      {event.agent && (
                        <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                          {event.agent}
                        </span>
                      )}
                      {event.tool && (
                        <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-800 rounded">
                          {event.tool}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900">{event.description}</p>
                  </div>
                  {event.details && (
                    <svg
                      className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${
                        expandedEvent === event.id ? 'transform rotate-180' : ''
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
              
              {expandedEvent === event.id && event.details && (
                <div className="event-details p-4 border-t border-gray-200 bg-gray-50">
                  <pre className="text-xs text-gray-700 overflow-x-auto">
                    {JSON.stringify(event.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

function EventIcon({ type }: { type: string }) {
  const iconClass = "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0";
  
  switch (type) {
    case 'agent_started':
      return (
        <div className={`${iconClass} bg-green-100`}>
          <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
      );
    case 'agent_finished':
      return (
        <div className={`${iconClass} bg-blue-100`}>
          <svg className="w-4 h-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        </div>
      );
    case 'tool_call':
      return (
        <div className={`${iconClass} bg-purple-100`}>
          <svg className="w-4 h-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
      );
    case 'file_operation':
      return (
        <div className={`${iconClass} bg-yellow-100`}>
          <svg className="w-4 h-4 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
      );
    case 'test_run':
      return (
        <div className={`${iconClass} bg-indigo-100`}>
          <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
          </svg>
        </div>
      );
    case 'error':
      return (
        <div className={`${iconClass} bg-red-100`}>
          <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        </div>
      );
    default:
      return (
        <div className={`${iconClass} bg-gray-100`}>
          <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="3" />
          </svg>
        </div>
      );
  }
}

function EventTypeBadge({ type }: { type: string }) {
  const classes: Record<string, string> = {
    'agent_started': 'bg-green-100 text-green-800',
    'agent_finished': 'bg-blue-100 text-blue-800',
    'tool_call': 'bg-purple-100 text-purple-800',
    'file_operation': 'bg-yellow-100 text-yellow-800',
    'test_run': 'bg-indigo-100 text-indigo-800',
    'error': 'bg-red-100 text-red-800',
    'thinking': 'bg-gray-100 text-gray-800',
  };
  
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${classes[type] || 'bg-gray-100 text-gray-800'}`}>
      {type.replace('_', ' ')}
    </span>
  );
}

export default EventsTab;