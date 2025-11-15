import React, { useState } from 'react';
import { RunMetadata, RunStage } from '../../../contexts/RunContext';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Button } from '../../ui/button';
import { Textarea } from '../../ui/textarea';
import axios from 'axios';

interface OverviewTabProps {
  run: {
    metadata: RunMetadata;
    stages: RunStage[];
    events: any[];
    files: any[];
    tests: any[];
  };
}

const OverviewTab: React.FC<OverviewTabProps> = ({ run }) => {
  const { metadata, stages } = run;
  const [isRerunDialogOpen, setIsRerunDialogOpen] = useState(false);
  const [isCloneDialogOpen, setIsCloneDialogOpen] = useState(false);
  const [editedPrompt, setEditedPrompt] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleRerun = () => {
    setEditedPrompt(metadata.inputMessage || '');
    setIsRerunDialogOpen(true);
  };

  const handleClone = () => {
    setEditedPrompt(metadata.inputMessage || '');
    setIsCloneDialogOpen(true);
  };
  
  const confirmRerun = async () => {
    try {
      setIsSubmitting(true);
      const response = await axios.post(`${BACKEND_URL}/api/runs/${metadata.runId}/rerun`, {
        prompt: editedPrompt
      });
      
      if (response.data.success) {
        alert(`✅ Task re-run started! New Task ID: ${response.data.new_task_id}`);
        setIsRerunDialogOpen(false);
      } else {
        alert(`❌ Failed to re-run: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Error re-running task:', error);
      alert('❌ Error starting re-run. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const confirmClone = async () => {
    try {
      setIsSubmitting(true);
      const response = await axios.post(`${BACKEND_URL}/api/runs/${metadata.runId}/rerun`, {
        prompt: editedPrompt
      });
      
      if (response.data.success) {
        alert(`✅ Cloned run started! New Task ID: ${response.data.new_task_id}`);
        setIsCloneDialogOpen(false);
      } else {
        alert(`❌ Failed to clone: ${response.data.error}`);
      }
    } catch (error) {
      console.error('Error cloning task:', error);
      alert('❌ Error cloning run. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="overview-tab p-6 space-y-6">
      {/* Summary Card */}
      <div className="summary-card bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Run Summary</h3>
        
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className={`text-lg font-medium ${getStatusColor(metadata.status)}`}>
              {metadata.status}
            </p>
          </div>
          
          <div>
            <p className="text-sm text-gray-500">Duration</p>
            <p className="text-lg font-medium text-gray-900">
              {formatDuration(metadata.duration)}
            </p>
          </div>
          
          {metadata.startTime && (
            <div>
              <p className="text-sm text-gray-500">Started</p>
              <p className="text-sm text-gray-900">
                {new Date(metadata.startTime).toLocaleString()}
              </p>
            </div>
          )}
          
          {metadata.endTime && (
            <div>
              <p className="text-sm text-gray-500">Ended</p>
              <p className="text-sm text-gray-900">
                {new Date(metadata.endTime).toLocaleString()}
              </p>
            </div>
          )}
          
          {metadata.tokens !== undefined && (
            <div>
              <p className="text-sm text-gray-500">Tokens Used</p>
              <p className="text-lg font-medium text-gray-900">
                {metadata.tokens.toLocaleString()}
              </p>
            </div>
          )}
          
          {metadata.cost !== undefined && (
            <div>
              <p className="text-sm text-gray-500">Cost</p>
              <p className="text-lg font-medium text-gray-900">
                ${metadata.cost.toFixed(4)}
              </p>
            </div>
          )}
        </div>

        {metadata.description && (
          <div className="mt-4">
            <p className="text-sm text-gray-500">Description</p>
            <p className="text-sm text-gray-900 mt-1">{metadata.description}</p>
          </div>
        )}
      </div>

      {/* Pipeline Visualization */}
      <div className="pipeline-card bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Pipeline</h3>
        
        <div className="pipeline-stages space-y-3">
          {stages.map((stage, index) => (
            <div key={stage.name} className="stage-item">
              <div className="flex items-center">
                {/* Stage Icon */}
                <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${getStageIconClass(stage.status)}`}>
                  {getStageIcon(stage.status)}
                </div>
                
                {/* Stage Details */}
                <div className="ml-4 flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{stage.name}</h4>
                      {stage.agent && (
                        <p className="text-xs text-gray-500">Agent: {stage.agent}</p>
                      )}
                    </div>
                    
                    <div className="text-right">
                      <span className={`text-xs font-medium ${getStageStatusColor(stage.status)}`}>
                        {stage.status.replace('_', ' ')}
                      </span>
                      {stage.startTime && stage.endTime && (
                        <p className="text-xs text-gray-500 mt-1">
                          {formatDuration(new Date(stage.endTime).getTime() - new Date(stage.startTime).getTime())}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Connector Line */}
              {index < stages.length - 1 && (
                <div className="ml-5 w-0.5 h-6 bg-gray-200"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="actions-card bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
        
        <div className="flex gap-3">
          <button
            onClick={handleRerun}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Re-run with same inputs
          </button>
          
          <button
            onClick={handleClone}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Clone to new run
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="metrics-card bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Run Metrics</h3>
        
        <div className="grid grid-cols-3 gap-4">
          <div className="metric-item text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{run.events.length}</p>
            <p className="text-sm text-gray-500 mt-1">Events</p>
          </div>
          
          <div className="metric-item text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{run.files.length}</p>
            <p className="text-sm text-gray-500 mt-1">Files Modified</p>
          </div>
          
          <div className="metric-item text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-2xl font-bold text-gray-900">{run.tests.length}</p>
            <p className="text-sm text-gray-500 mt-1">Tests Run</p>
          </div>
        </div>
      </div>
      
      {/* Re-run Dialog */}
      <Dialog open={isRerunDialogOpen} onOpenChange={setIsRerunDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Re-run Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Edit prompt (optional)
              </label>
              <Textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                rows={6}
                className="w-full"
                placeholder="Enter your task description..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRerunDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmRerun} disabled={isSubmitting}>
              {isSubmitting ? 'Starting...' : 'Start Re-run'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Clone Dialog */}
      <Dialog open={isCloneDialogOpen} onOpenChange={setIsCloneDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Clone Run</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Edit prompt for new run
              </label>
              <Textarea
                value={editedPrompt}
                onChange={(e) => setEditedPrompt(e.target.value)}
                rows={6}
                className="w-full"
                placeholder="Enter your task description..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCloneDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={confirmClone} disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Clone'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

function getStatusColor(status: string): string {
  switch (status) {
    case 'succeeded':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'running':
      return 'text-blue-600';
    case 'queued':
      return 'text-yellow-600';
    case 'cancelled':
      return 'text-gray-600';
    default:
      return 'text-gray-600';
  }
}

function getStageIconClass(status: string): string {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-600';
    case 'failed':
      return 'bg-red-100 text-red-600';
    case 'running':
      return 'bg-blue-100 text-blue-600 animate-pulse';
    case 'not_started':
      return 'bg-gray-100 text-gray-400';
    default:
      return 'bg-gray-100 text-gray-400';
  }
}

function getStageIcon(status: string): React.ReactNode {
  switch (status) {
    case 'success':
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    case 'failed':
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      );
    case 'running':
      return (
        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      );
    default:
      return (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <circle cx="10" cy="10" r="3" />
        </svg>
      );
  }
}

function getStageStatusColor(status: string): string {
  switch (status) {
    case 'success':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'running':
      return 'text-blue-600';
    case 'not_started':
      return 'text-gray-400';
    default:
      return 'text-gray-400';
  }
}

export default OverviewTab;
