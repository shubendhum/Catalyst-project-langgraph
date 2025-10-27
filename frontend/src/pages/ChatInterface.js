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
  
  const [llmConfig, setLlmConfig] = useState({
    provider: 'emergent',
    model: 'claude-3-7-sonnet-20250219',
    anthropic_api_key: '',
    aws_access_key_id: '',
    aws_secret_access_key: '',
    aws_region: 'us-east-1',
    aws_endpoint_url: '',
    bedrock_model_id: 'anthropic.claude-3-sonnet-20240229-v1:0',
    // Organization Azure OpenAI (OAuth2)
    org_azure_base_url: '',
    org_azure_deployment: '',
    org_azure_api_version: '2024-02-15-preview',
    org_azure_subscription_key: '',
    oauth_auth_url: '',
    oauth_token_url: '',
    oauth_client_id: '',
    oauth_client_secret: '',
    oauth_redirect_uri: 'http://localhost:8001/api/auth/oauth/callback',
    oauth_scopes: '',
    emergent_key_available: false,
    oauth_authenticated: false  // Track OAuth2 authentication status
  });

  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const messagesEndRef = useRef(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Cleanup websocket on unmount
  useEffect(() => {
    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [websocket]);

  const connectWebSocket = (taskId) => {
    // Close existing websocket if any
    if (websocket) {
      websocket.close();
    }

    // Create WebSocket URL (replace https with wss)
    const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');
    const ws = new WebSocket(`${wsUrl}/ws/${taskId}`);

    ws.onopen = () => {
      console.log(`✅ WebSocket connected for task ${taskId}`);
    };

    ws.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data);
        
        // Check if this is a completion message
        if (logData.message && logData.message.includes('completed successfully')) {
          setActiveTaskId(null);
          setIsLoading(false);
          addSystemMessage(`✅ ${logData.agent_name}: ${logData.message}`);
        } else {
          // Add agent log as system message with formatting
          const agentMessage = `🤖 **${logData.agent_name}**: ${logData.message}`;
          addSystemMessage(agentMessage);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setActiveTaskId(null);
      setIsLoading(false);
    };

    setWebsocket(ws);
  };

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

  const startOAuthFlow = async () => {
    try {
      setIsAuthenticating(true);
      
      // Get authorization URL from backend
      const response = await axios.post(`${BACKEND_URL}/api/auth/oauth/start`, {
        auth_url: llmConfig.oauth_auth_url,
        client_id: llmConfig.oauth_client_id,
        redirect_uri: llmConfig.oauth_redirect_uri,
        scopes: llmConfig.oauth_scopes
      });
      
      const authUrl = response.data.authorization_url;
      const state = response.data.state;
      
      // Open auth URL in popup
      const width = 600;
      const height = 700;
      const left = (window.screen.width - width) / 2;
      const top = (window.screen.height - height) / 2;
      
      const authWindow = window.open(
        authUrl,
        'OAuth2 Authentication',
        `width=${width},height=${height},left=${left},top=${top}`
      );
      
      // Poll for auth completion
      const checkAuth = setInterval(async () => {
        try {
          const statusResponse = await axios.get(`${BACKEND_URL}/api/auth/oauth/status?state=${state}`);
          
          if (statusResponse.data.authenticated) {
            clearInterval(checkAuth);
            setIsAuthenticating(false);
            setLlmConfig({...llmConfig, oauth_authenticated: true});
            addSystemMessage('✅ OAuth2 authentication successful!');
            
            if (authWindow && !authWindow.closed) {
              authWindow.close();
            }
          } else if (statusResponse.data.error) {
            clearInterval(checkAuth);
            setIsAuthenticating(false);
            addSystemMessage(`❌ OAuth2 authentication failed: ${statusResponse.data.error}`);
            
            if (authWindow && !authWindow.closed) {
              authWindow.close();
            }
          }
        } catch (err) {
          // Continue polling
        }
      }, 1000);
      
      // Stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(checkAuth);
        setIsAuthenticating(false);
      }, 300000);
      
    } catch (error) {
      console.error('Error starting OAuth flow:', error);
      setIsAuthenticating(false);
      addSystemMessage('Error starting OAuth2 authentication.');
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
      
      // Check if a task was started
      const metadata = response.data.message.metadata || {};
      if (metadata.action === 'task_started' && metadata.task_id) {
        // Connect WebSocket for real-time updates
        setActiveTaskId(metadata.task_id);
        connectWebSocket(metadata.task_id);
        addSystemMessage('📡 Connected to live updates - you\'ll see progress in real-time...');
        // Keep loading state active until task completes
      } else {
        // No task started, just normal chat
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addSystemMessage('Error sending message. Please try again.');
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
                    <SelectItem value="org_azure">Organization Azure OpenAI (OAuth2)</SelectItem>
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

              {llmConfig.provider === 'org_azure' && (
                <>
                  <div style={{ padding: '12px', backgroundColor: '#eff6ff', border: '1px solid #3b82f6', borderRadius: '6px', marginBottom: '16px' }}>
                    <strong style={{ color: '#1e40af' }}>Organization Azure OpenAI with OAuth2</strong>
                    <p style={{ fontSize: '13px', color: '#1e40af', margin: '4px 0 0 0' }}>
                      Automatic authentication via OAuth2. Token managed automatically.
                    </p>
                  </div>

                  <div>
                    <Label>Base URL</Label>
                    <Input 
                      value={llmConfig.org_azure_base_url}
                      onChange={(e) => setLlmConfig({...llmConfig, org_azure_base_url: e.target.value})}
                      placeholder="https://api.macquarie.com"
                    />
                  </div>

                  <div>
                    <Label>Deployment Name</Label>
                    <Input 
                      value={llmConfig.org_azure_deployment}
                      onChange={(e) => setLlmConfig({...llmConfig, org_azure_deployment: e.target.value})}
                      placeholder="gpt-4 or gpt-35-turbo"
                    />
                  </div>

                  <div>
                    <Label>API Version</Label>
                    <Input 
                      value={llmConfig.org_azure_api_version}
                      onChange={(e) => setLlmConfig({...llmConfig, org_azure_api_version: e.target.value})}
                      placeholder="2024-02-15-preview"
                    />
                  </div>

                  <div>
                    <Label>Subscription Key (Ocp-Apim-Subscription-Key)</Label>
                    <Input 
                      type="password"
                      value={llmConfig.org_azure_subscription_key}
                      onChange={(e) => setLlmConfig({...llmConfig, org_azure_subscription_key: e.target.value})}
                      placeholder="Your subscription key"
                    />
                  </div>

                  <hr style={{ margin: '16px 0', borderColor: '#e5e7eb' }} />

                  <div style={{ marginBottom: '8px' }}>
                    <strong style={{ fontSize: '14px', color: '#374151' }}>OAuth2 Configuration</strong>
                  </div>

                  <div>
                    <Label>Authorization URL</Label>
                    <Input 
                      value={llmConfig.oauth_auth_url}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_auth_url: e.target.value})}
                      placeholder="https://login.microsoftonline.com/.../oauth2/v2.0/authorize"
                    />
                  </div>

                  <div>
                    <Label>Token URL</Label>
                    <Input 
                      value={llmConfig.oauth_token_url}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_token_url: e.target.value})}
                      placeholder="https://login.microsoftonline.com/.../oauth2/v2.0/token"
                    />
                  </div>

                  <div>
                    <Label>Client ID</Label>
                    <Input 
                      value={llmConfig.oauth_client_id}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_client_id: e.target.value})}
                      placeholder="Your OAuth2 client ID"
                    />
                  </div>

                  <div>
                    <Label>Client Secret</Label>
                    <Input 
                      type="password"
                      value={llmConfig.oauth_client_secret}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_client_secret: e.target.value})}
                      placeholder="Your OAuth2 client secret"
                    />
                  </div>

                  <div>
                    <Label>Scopes (space-separated)</Label>
                    <Input 
                      value={llmConfig.oauth_scopes}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_scopes: e.target.value})}
                      placeholder="api://xxx/.default"
                    />
                  </div>

                  <div>
                    <Label>Redirect URI</Label>
                    <Input 
                      value={llmConfig.oauth_redirect_uri}
                      onChange={(e) => setLlmConfig({...llmConfig, oauth_redirect_uri: e.target.value})}
                      placeholder="http://localhost:8001/api/auth/oauth/callback"
                    />
                    <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                      Must match redirect URI configured in OAuth2 app
                    </p>
                  </div>

                  <hr style={{ margin: '16px 0', borderColor: '#e5e7eb' }} />

                  <div style={{ padding: '12px', backgroundColor: llmConfig.oauth_authenticated ? '#f0fdf4' : '#fef3c7', border: `1px solid ${llmConfig.oauth_authenticated ? '#86efac' : '#fcd34d'}`, borderRadius: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                      <span style={{ fontSize: '18px' }}>
                        {llmConfig.oauth_authenticated ? '✅' : '🔐'}
                      </span>
                      <strong style={{ color: llmConfig.oauth_authenticated ? '#16a34a' : '#ca8a04' }}>
                        {llmConfig.oauth_authenticated ? 'Authenticated' : 'Authentication Required'}
                      </strong>
                    </div>
                    {!llmConfig.oauth_authenticated && (
                      <>
                        <p style={{ fontSize: '13px', color: '#92400e', marginBottom: '12px' }}>
                          Click the button below to authenticate with your organization's credentials
                        </p>
                        <Button 
                          onClick={startOAuthFlow}
                          disabled={isAuthenticating || !llmConfig.oauth_auth_url || !llmConfig.oauth_client_id}
                          className="btn-primary"
                          style={{ width: '100%' }}
                        >
                          {isAuthenticating ? (
                            <>
                              <Loader2 size={16} className="animate-spin" style={{ marginRight: '8px' }} />
                              Authenticating...
                            </>
                          ) : (
                            '🔐 Authenticate with Organization'
                          )}
                        </Button>
                      </>
                    )}
                    {llmConfig.oauth_authenticated && (
                      <p style={{ fontSize: '13px', color: '#166534' }}>
                        You're authenticated! Token will auto-refresh when needed.
                      </p>
                    )}
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
              background: 'rgba(34, 197, 94, 0.1)', 
              borderRadius: '8px'
            }}>
              <div style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: '#22c55e',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
              }} />
            </div>
            <div style={{
              padding: '12px 16px',
              borderRadius: '12px',
              background: 'rgba(34, 197, 94, 0.05)',
              border: '1px solid rgba(34, 197, 94, 0.2)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Loader2 size={16} className="animate-spin" style={{ color: '#22c55e' }} />
              <span style={{ color: '#22c55e', fontWeight: '500' }}>
                {activeTaskId ? 'Agent is running...' : 'Thinking...'}
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ 
        padding: '16px 24px', 
        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
        background: activeTaskId ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        opacity: activeTaskId ? 0.6 : 1,
        transition: 'all 0.3s ease'
      }}>
        {activeTaskId && (
          <div style={{
            textAlign: 'center',
            marginBottom: '12px',
            padding: '8px 16px',
            background: 'rgba(34, 197, 94, 0.1)',
            borderRadius: '8px',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            display: 'inline-block',
            marginLeft: 'auto',
            marginRight: 'auto',
            width: '100%'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: '#22c55e',
                animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
              }} />
              <span style={{ color: '#22c55e', fontSize: '14px', fontWeight: '500' }}>
                Agent is working on your request...
              </span>
            </div>
          </div>
        )}
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
            placeholder={activeTaskId ? "Agent is running... Please wait" : "Type your message... (Press Enter to send)"}
            disabled={isLoading || activeTaskId}
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
            disabled={isLoading || !inputMessage.trim() || activeTaskId}
            className="btn-primary"
            style={{ 
              padding: '12px 24px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              opacity: activeTaskId ? 0.5 : 1
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
