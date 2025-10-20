import React, { useState, useEffect, useRef } from 'react';
import { Send, Settings, Bot, User, Loader2, BarChart3, FileText, Plus, MessageSquare } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Link } from 'react-router-dom';
import axios from 'axios';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [websocket, setWebsocket] = useState(null);
  
  // LLM Settings
  const [llmConfig, setLlmConfig] = useState({
    provider: 'emergent',
    model: 'claude-3-7-sonnet-20250219',
    anthropic_api_key: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: 'us-east-1',
    aws_endpoint_url: '',
    bedrock_model_id: 'anthropic.claude-3-sonnet-20240229-v1:0',
    emergent_key_available: false
  });

  const messagesEndRef = useRef(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load current LLM config and restore conversation on mount
  useEffect(() => {
    loadLLMConfig();
    loadOrCreateConversation();
  }, []);

  const loadOrCreateConversation = async () => {
    // Try to get conversation ID from localStorage
    const savedConversationId = localStorage.getItem('catalyst_conversation_id');
    
    if (savedConversationId) {
      // Try to load existing conversation
      try {
        const response = await axios.get(`${BACKEND_URL}/api/chat/conversations/${savedConversationId}`);
        if (response.data && response.data.messages) {
          setConversationId(savedConversationId);
          // Load messages from backend
          const loadedMessages = response.data.messages.map(msg => ({
            role: msg.role,
            content: msg.content,
            timestamp: msg.timestamp
          }));
          setMessages(loadedMessages);
          console.log(`✅ Loaded ${loadedMessages.length} messages from conversation ${savedConversationId}`);
          return;
        }
      } catch (error) {
        console.warn('Failed to load previous conversation:', error);
        // Continue to create new conversation
      }
    }
    
    // No saved conversation or failed to load - add welcome message
    addSystemMessage("👋 Welcome to Catalyst! I can help you build applications, analyze repositories, and more. What would you like to create today?");
  };

  const loadLLMConfig = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/chat/config`);
      if (response.data) {
        setLlmConfig(response.data);
        // Show notification if Emergent key is available
        if (response.data.emergent_key_available) {
          console.log('✅ Emergent LLM Key detected and configured');
        }
      }
    } catch (error) {
      console.error('Error loading LLM config:', error);
      addSystemMessage("⚠️ Failed to load LLM configuration. Please check settings.");
    }
  };

  const saveLLMConfig = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/chat/config`, llmConfig);
      setIsSettingsOpen(false);
      // Show success message
      addSystemMessage('LLM configuration updated successfully!');
    } catch (error) {
      console.error('Error saving LLM config:', error);
      addSystemMessage('Error updating LLM configuration. Please try again.');
    }
  };

  const addSystemMessage = (content) => {
    setMessages(prev => [...prev, {
      role: 'system',
      content,
      timestamp: new Date().toISOString()
    }]);
  };

  const startNewConversation = async () => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/chat/conversations`, {
        title: 'New Conversation'
      });
      const newConversationId = response.data.id;
      setConversationId(newConversationId);
      
      // Save to localStorage for persistence
      localStorage.setItem('catalyst_conversation_id', newConversationId);
      
      setMessages([]);
      addSystemMessage('🆕 New conversation started. How can I help you today?');
      return newConversationId;
    } catch (error) {
      console.error('Error starting conversation:', error);
      addSystemMessage('Error starting conversation. Please check your backend connection.');
      return null;
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Start a new conversation if one doesn't exist
      let currentConvId = conversationId;
      if (!currentConvId) {
        currentConvId = await startNewConversation();
        if (!currentConvId) {
          setIsLoading(false);
          return;
        }
      } else {
        // Save existing conversation ID to localStorage
        localStorage.setItem('catalyst_conversation_id', currentConvId);
      }

      // Send message to backend
      const response = await axios.post(`${BACKEND_URL}/api/chat/send`, {
        conversation_id: currentConvId,
        message: inputMessage
      });

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.data.message.content,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      addSystemMessage('Error sending message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#0f172a' }}>
      {/* Header */}
      <div style={{ 
        padding: '16px 24px', 
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Bot size={32} style={{ color: '#63b3ed' }} />
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#fff' }}>Catalyst AI</h1>
            <p style={{ fontSize: '12px', color: '#94a3b8' }}>Multi-Agent Development Platform</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Button 
            variant="outline" 
            onClick={startNewConversation}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            title="Start New Conversation"
          >
            <Plus size={18} />
            New Chat
          </Button>
          <Link to="/costs" style={{ textDecoration: 'none' }}>
            <Button variant="outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart3 size={18} />
              Cost Dashboard
            </Button>
          </Link>
          <Link to="/logs" style={{ textDecoration: 'none' }}>
            <Button variant="outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} />
              Backend Logs
            </Button>
          </Link>
          <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Settings size={18} />
                LLM Settings
              </Button>
            </DialogTrigger>
          <DialogContent className="glass-strong" style={{ maxWidth: '500px', maxHeight: '80vh', overflowY: 'auto' }}>
            <DialogHeader>
              <DialogTitle>LLM Configuration</DialogTitle>
            </DialogHeader>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px 0' }}>
              <div>
                <Label>Provider</Label>
                <Select 
                  value={llmConfig.provider} 
                  onValueChange={(value) => setLlmConfig({...llmConfig, provider: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="emergent">Emergent (Universal Key)</SelectItem>
                    <SelectItem value="anthropic">Anthropic Claude</SelectItem>
                    <SelectItem value="bedrock">AWS Bedrock</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Model</Label>
                <Input 
                  value={llmConfig.model}
                  onChange={(e) => setLlmConfig({...llmConfig, model: e.target.value})}
                  placeholder="claude-3-7-sonnet-20250219"
                />
              </div>

              {llmConfig.provider === 'emergent' && (
                <div style={{ padding: '12px', backgroundColor: '#f0fdf4', border: '1px solid #86efac', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '18px' }}>
                      {llmConfig.emergent_key_available ? '✅' : '⚠️'}
                    </span>
                    <strong style={{ color: llmConfig.emergent_key_available ? '#16a34a' : '#ea580c' }}>
                      {llmConfig.emergent_key_available ? 'Emergent LLM Key Configured' : 'Emergent LLM Key Not Found'}
                    </strong>
                  </div>
                  <p style={{ fontSize: '13px', color: '#65a30d', margin: 0 }}>
                    {llmConfig.emergent_key_available 
                      ? 'Using your universal key for OpenAI, Anthropic, and Google models.'
                      : 'Please configure EMERGENT_LLM_KEY in backend .env file.'}
                  </p>
                </div>
              )}

              {llmConfig.provider === 'anthropic' && (
                <div>
                  <Label>Anthropic API Key</Label>
                  <Input 
                    type="password"
                    value={llmConfig.anthropic_api_key}
                    onChange={(e) => setLlmConfig({...llmConfig, anthropic_api_key: e.target.value})}
                    placeholder="sk-ant-..."
                  />
                </div>
              )}

              {llmConfig.provider === 'bedrock' && (
                <>
                  <div>
                    <Label>AWS Access Key ID</Label>
                    <Input 
                      type="password"
                      value={llmConfig.aws_access_key_id}
                      onChange={(e) => setLlmConfig({...llmConfig, aws_access_key_id: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>AWS Secret Access Key</Label>
                    <Input 
                      type="password"
                      value={llmConfig.aws_secret_access_key}
                      onChange={(e) => setLlmConfig({...llmConfig, aws_secret_access_key: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>AWS Region</Label>
                    <Input 
                      value={llmConfig.aws_region}
                      onChange={(e) => setLlmConfig({...llmConfig, aws_region: e.target.value})}
                      placeholder="us-east-1"
                    />
                  </div>
                  <div>
                    <Label>AWS Endpoint URL (Optional)</Label>
                    <Input 
                      value={llmConfig.aws_endpoint_url}
                      onChange={(e) => setLlmConfig({...llmConfig, aws_endpoint_url: e.target.value})}
                      placeholder="https://bedrock.vpce-xxxxx.region.vpce.amazonaws.com"
                    />
                    <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                      For VPC endpoints or organization-specific AWS URLs
                    </p>
                  </div>
                  <div>
                    <Label>Bedrock Model ID</Label>
                    <Input 
                      value={llmConfig.bedrock_model_id}
                      onChange={(e) => setLlmConfig({...llmConfig, bedrock_model_id: e.target.value})}
                      placeholder="anthropic.claude-3-sonnet-20240229-v1:0"
                    />
                  </div>
                </>
              )}

              <Button onClick={saveLLMConfig} className="btn-primary" style={{ marginTop: '8px' }}>
                Save Configuration
              </Button>
            </div>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      {/* Messages Area */}
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        {messages.length === 0 && (
          <div style={{ 
            flex: 1, 
            display: 'flex', 
            flexDirection: 'column',
            alignItems: 'center', 
            justifyContent: 'center',
            gap: '16px'
          }}>
            <Bot size={64} style={{ color: '#63b3ed', opacity: 0.5 }} />
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#cbd5e1' }}>
              Welcome to Catalyst AI
            </h2>
            <p style={{ color: '#64748b', textAlign: 'center', maxWidth: '500px' }}>
              Start a conversation to create projects, build applications, or get help with development tasks.
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div 
            key={index}
            style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start',
              justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            {message.role === 'assistant' && (
              <div style={{ 
                padding: '8px', 
                background: 'rgba(99, 179, 237, 0.1)', 
                borderRadius: '8px',
                flexShrink: 0
              }}>
                <Bot size={20} style={{ color: '#63b3ed' }} />
              </div>
            )}
            
            {message.role === 'system' && (
              <div style={{ 
                padding: '8px', 
                background: 'rgba(245, 158, 11, 0.1)', 
                borderRadius: '8px',
                flexShrink: 0
              }}>
                <Settings size={20} style={{ color: '#f59e0b' }} />
              </div>
            )}

            <div 
              style={{
                maxWidth: '70%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: message.role === 'user' 
                  ? 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
                  : message.role === 'system'
                  ? 'rgba(245, 158, 11, 0.1)'
                  : 'rgba(255, 255, 255, 0.05)',
                border: message.role !== 'user' ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
                color: '#fff',
                wordWrap: 'break-word'
              }}
            >
              <p style={{ margin: 0, lineHeight: '1.6' }}>{message.content}</p>
              <span style={{ 
                fontSize: '11px', 
                color: message.role === 'user' ? 'rgba(255,255,255,0.7)' : '#64748b',
                display: 'block',
                marginTop: '8px'
              }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {message.role === 'user' && (
              <div style={{ 
                padding: '8px', 
                background: 'rgba(59, 130, 246, 0.1)', 
                borderRadius: '8px',
                flexShrink: 0
              }}>
                <User size={20} style={{ color: '#3b82f6' }} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ 
              padding: '8px', 
              background: 'rgba(99, 179, 237, 0.1)', 
              borderRadius: '8px'
            }}>
              <Bot size={20} style={{ color: '#63b3ed' }} />
            </div>
            <div style={{
              padding: '12px 16px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Loader2 size={16} className="animate-spin" style={{ color: '#63b3ed' }} />
              <span style={{ color: '#94a3b8' }}>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ 
        padding: '16px 24px', 
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)'
      }}>
        <div style={{ 
          maxWidth: '900px', 
          margin: '0 auto',
          display: 'flex',
          gap: '12px',
          alignItems: 'center'
        }}>
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Press Enter to send)"
            disabled={isLoading}
            style={{ 
              flex: 1,
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#fff',
              padding: '12px 16px'
            }}
          />
          <Button 
            onClick={sendMessage}
            disabled={isLoading || !inputMessage.trim()}
            className="btn-primary"
            style={{ 
              padding: '12px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            {isLoading ? (
              <Loader2 size={18} className="animate-spin" />
            ) : (
              <Send size={18} />
            )}
            Send
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
