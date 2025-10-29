import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Code, Eye, Save, Edit, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

const ThinkingBlock = ({ content, isExpanded: initialExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  
  return (
    <div className="my-2 border border-blue-200 rounded-lg bg-blue-50 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-blue-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <span className="font-medium text-blue-900">💭 Thinking...</span>
        </div>
      </button>
      {isExpanded && (
        <div className="px-4 py-3 border-t border-blue-200 bg-white">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
            {content}
          </pre>
        </div>
      )}
    </div>
  );
};

const ToolCall = ({ tool, args, isExpanded: initialExpanded = true }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  
  const getToolIcon = (toolName) => {
    if (toolName.includes('view') || toolName.includes('read')) return <Eye className="w-4 h-4" />;
    if (toolName.includes('edit') || toolName.includes('replace')) return <Edit className="w-4 h-4" />;
    if (toolName.includes('create') || toolName.includes('write')) return <Save className="w-4 h-4" />;
    return <Code className="w-4 h-4" />;
  };

  const getToolColor = (toolName) => {
    if (toolName.includes('view') || toolName.includes('read')) return 'bg-purple-50 border-purple-200';
    if (toolName.includes('edit') || toolName.includes('replace')) return 'bg-orange-50 border-orange-200';
    if (toolName.includes('create') || toolName.includes('write')) return 'bg-green-50 border-green-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className={`my-2 border rounded-lg overflow-hidden ${getToolColor(tool)}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2 flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <div className="flex items-center gap-2">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          {getToolIcon(tool)}
          <span className="font-medium">{tool}</span>
        </div>
      </button>
      {isExpanded && (
        <div className="px-4 py-3 border-t bg-white">
          <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono overflow-x-auto">
            {JSON.stringify(args, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

const FileOperation = ({ operation, filePath, status = 'success' }) => {
  const getOperationIcon = () => {
    switch (operation) {
      case 'view': return <Eye className="w-4 h-4" />;
      case 'edit': return <Edit className="w-4 h-4" />;
      case 'create': return <Save className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  const getOperationColor = () => {
    switch (operation) {
      case 'view': return 'text-purple-600 bg-purple-50';
      case 'edit': return 'text-orange-600 bg-orange-50';
      case 'create': return 'text-green-600 bg-green-50';
      default: return 'text-blue-600 bg-blue-50';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'loading': return <Loader2 className="w-3 h-3 animate-spin" />;
      case 'success': return <CheckCircle className="w-3 h-3 text-green-500" />;
      case 'error': return <AlertCircle className="w-3 h-3 text-red-500" />;
      default: return null;
    }
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg ${getOperationColor()} my-1 mr-2`}>
      {getOperationIcon()}
      <span className="text-sm font-medium">{operation}</span>
      <a 
        href="#" 
        className="text-sm underline hover:no-underline"
        onClick={(e) => {
          e.preventDefault();
          // TODO: Open file viewer/editor
          console.log('View file:', filePath);
        }}
      >
        {filePath}
      </a>
      {getStatusIcon()}
    </div>
  );
};

const AgentProgress = ({ agentName, status, message, progress }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed': return 'text-green-600 bg-green-50 border-green-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'waiting': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'running': return <Loader2 className="w-4 h-4 animate-spin" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <div className="w-4 h-4 rounded-full border-2 border-current" />;
    }
  };

  return (
    <div className={`border rounded-lg p-3 ${getStatusColor()}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <span className="font-semibold">{agentName}</span>
        </div>
        {progress !== undefined && (
          <span className="text-sm font-medium">{progress}%</span>
        )}
      </div>
      {message && (
        <p className="text-sm ml-6">{message}</p>
      )}
      {progress !== undefined && status === 'running' && (
        <div className="mt-2 ml-6">
          <div className="w-full bg-white rounded-full h-1.5">
            <div 
              className="bg-current h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const CodeBlock = ({ code, language = 'javascript' }) => {
  return (
    <div className="my-2 rounded-lg overflow-hidden border border-gray-200">
      <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
        <span className="text-xs text-gray-400 font-mono">{language}</span>
        <button
          onClick={() => {
            navigator.clipboard.writeText(code);
          }}
          className="text-xs text-gray-400 hover:text-white transition-colors"
        >
          Copy
        </button>
      </div>
      <pre className="p-4 bg-gray-900 text-gray-100 text-sm overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export { ThinkingBlock, ToolCall, FileOperation, AgentProgress, CodeBlock };
