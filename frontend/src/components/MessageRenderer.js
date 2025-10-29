import React from 'react';
import { ThinkingBlock, ToolCall, FileOperation, AgentProgress, CodeBlock } from './ChatComponents';
import { Bot, User } from 'lucide-react';
import './MessageRenderer.css';

const MessageRenderer = ({ message }) => {
  const { role, content, metadata } = message;

  const parseContent = (text) => {
    const elements = [];
    let remainingText = text;

    // Parse thinking blocks: <thinking>...</thinking>
    const thinkingRegex = /<thinking>([\s\S]*?)<\/thinking>/g;
    let match;
    let lastIndex = 0;

    while ((match = thinkingRegex.exec(text)) !== null) {
      // Add text before thinking block
      if (match.index > lastIndex) {
        elements.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        });
      }

      // Add thinking block
      elements.push({
        type: 'thinking',
        content: match[1].trim()
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      elements.push({
        type: 'text',
        content: text.substring(lastIndex)
      });
    }

    return elements.length > 0 ? elements : [{ type: 'text', content: text }];
  };

  const parseTextForCode = (text) => {
    // Parse code blocks: ```language\ncode\n```
    const codeRegex = /```(\w+)?\n([\s\S]*?)```/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = codeRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index)
        });
      }

      // Add code block
      parts.push({
        type: 'code',
        language: match[1] || 'text',
        content: match[2].trim()
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex)
      });
    }

    return parts.length > 0 ? parts : [{ type: 'text', content: text }];
  };

  const renderToolCalls = () => {
    if (!metadata?.tool_calls || metadata.tool_calls.length === 0) return null;

    return (
      <div className="space-y-2 mt-2">
        {metadata.tool_calls.map((toolCall, idx) => (
          <ToolCall
            key={idx}
            tool={toolCall.name}
            args={toolCall.arguments}
          />
        ))}
      </div>
    );
  };

  const renderFileOperations = () => {
    if (!metadata?.file_operations || metadata.file_operations.length === 0) return null;

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {metadata.file_operations.map((op, idx) => (
          <FileOperation
            key={idx}
            operation={op.operation}
            filePath={op.path}
            status={op.status}
          />
        ))}
      </div>
    );
  };

  const renderAgentProgress = () => {
    if (!metadata?.agent_progress) return null;

    return (
      <div className="space-y-2 mt-2">
        {Object.entries(metadata.agent_progress).map(([agentName, data]) => (
          <AgentProgress
            key={agentName}
            agentName={agentName}
            status={data.status}
            message={data.message}
            progress={data.progress}
          />
        ))}
      </div>
    );
  };

  const renderContent = () => {
    const elements = parseContent(content);

    return elements.map((element, idx) => {
      if (element.type === 'thinking') {
        return <ThinkingBlock key={idx} content={element.content} />;
      }

      // Parse text for code blocks
      const textParts = parseTextForCode(element.content);
      return textParts.map((part, partIdx) => {
        if (part.type === 'code') {
          return <CodeBlock key={`${idx}-${partIdx}`} code={part.content} language={part.language} />;
        }
        
        // Regular text with markdown support
        return (
          <div 
            key={`${idx}-${partIdx}`} 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ 
              __html: part.content
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/`(.*?)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
                .replace(/\n/g, '<br />')
            }}
          />
        );
      });
    });
  };

  return (
    <div className={`message-container ${role === 'user' ? 'message-user' : 'message-assistant'}`}>
      {role === 'assistant' && (
        <div className="message-avatar avatar-assistant">
          <Bot className="avatar-icon" />
        </div>
      )}
      
      <div className="message-content-wrapper">
        <div className={`message-bubble ${role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
          {renderContent()}
          {renderToolCalls()}
          {renderFileOperations()}
        </div>
        {renderAgentProgress()}
      </div>

      {role === 'user' && (
        <div className="message-avatar avatar-user">
          <User className="avatar-icon" />
        </div>
      )}
    </div>
  );
};

export default MessageRenderer;
