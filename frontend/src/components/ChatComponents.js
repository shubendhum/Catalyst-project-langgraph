import React, { useState } from 'react';
import { ChevronDown, ChevronRight, FileText, Code, Eye, Save, Edit, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import './ChatComponents.css';

const ThinkingBlock = ({ content, isExpanded: initialExpanded = false }) => {
  const [isExpanded, setIsExpanded] = useState(initialExpanded);
  
  return (
    <div className="thinking-block">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="thinking-header"
      >
        <div className="thinking-title">
          {isExpanded ? <ChevronDown className="icon-sm" /> : <ChevronRight className="icon-sm" />}
          <span className="thinking-label">💭 Thinking...</span>
        </div>
      </button>
      {isExpanded && (
        <div className="thinking-content">
          <pre className="thinking-text">
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
    if (toolName.includes('view') || toolName.includes('read')) return <Eye className="icon-sm" />;
    if (toolName.includes('edit') || toolName.includes('replace')) return <Edit className="icon-sm" />;
    if (toolName.includes('create') || toolName.includes('write')) return <Save className="icon-sm" />;
    return <Code className="icon-sm" />;
  };

  const getToolColorClass = (toolName) => {
    if (toolName.includes('view') || toolName.includes('read')) return 'tool-view';
    if (toolName.includes('edit') || toolName.includes('replace')) return 'tool-edit';
    if (toolName.includes('create') || toolName.includes('write')) return 'tool-create';
    return 'tool-default';
  };

  return (
    <div className={`tool-call ${getToolColorClass(tool)}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="tool-header"
      >
        <div className="tool-title">
          {isExpanded ? <ChevronDown className="icon-sm" /> : <ChevronRight className="icon-sm" />}
          {getToolIcon(tool)}
          <span className="tool-name">{tool}</span>
        </div>
      </button>
      {isExpanded && (
        <div className="tool-content">
          <pre className="tool-args">
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
      case 'view': return <Eye className="icon-sm" />;
      case 'edit': return <Edit className="icon-sm" />;
      case 'create': return <Save className="icon-sm" />;
      default: return <FileText className="icon-sm" />;
    }
  };

  const getOperationClass = () => {
    return `file-op file-op-${operation}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'loading': return <Loader2 className="icon-xs animate-spin" />;
      case 'success': return <CheckCircle className="icon-xs status-success" />;
      case 'error': return <AlertCircle className="icon-xs status-error" />;
      default: return null;
    }
  };

  return (
    <div className={getOperationClass()}>
      {getOperationIcon()}
      <span className="file-op-type">{operation}</span>
      <a 
        href="#" 
        className="file-op-path"
        onClick={(e) => {
          e.preventDefault();
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
  const getStatusClass = () => {
    return `agent-progress agent-${status}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'running': return <Loader2 className="icon-sm animate-spin" />;
      case 'completed': return <CheckCircle className="icon-sm" />;
      case 'error': return <AlertCircle className="icon-sm" />;
      default: return <div className="status-waiting" />;
    }
  };

  return (
    <div className={getStatusClass()}>
      <div className="agent-header">
        <div className="agent-title">
          {getStatusIcon()}
          <span className="agent-name">{agentName}</span>
        </div>
        {progress !== undefined && (
          <span className="agent-percentage">{progress}%</span>
        )}
      </div>
      {message && (
        <p className="agent-message">{message}</p>
      )}
      {progress !== undefined && status === 'running' && (
        <div className="agent-progress-bar">
          <div className="progress-track">
            <div 
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

const CodeBlock = ({ code, language = 'javascript' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-language">{language}</span>
        <button onClick={handleCopy} className="code-copy">
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="code-content">
        <code>{code}</code>
      </pre>
    </div>
  );
};

export { ThinkingBlock, ToolCall, FileOperation, AgentProgress, CodeBlock };
