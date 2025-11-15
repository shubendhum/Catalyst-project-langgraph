import React, { useState, useEffect } from 'react';
import './LLMConfigPanel.css';

interface LLMConfig {
  model: string;
  temperature: number;
  max_tokens: number;
  router_policy: string;
  provider?: string;
}

interface Model {
  id: string;
  name: string;
  context_window: number;
}

interface RouterPolicy {
  id: string;
  name: string;
  description: string;
}

interface LLMConfigPanelProps {
  onClose?: () => void;
}

const LLMConfigPanel: React.FC<LLMConfigPanelProps> = ({ onClose }) => {
  const [config, setConfig] = useState<LLMConfig>({
    model: 'claude-3-7-sonnet-20250219',
    temperature: 0.7,
    max_tokens: 4096,
    router_policy: 'smart',
    provider: 'emergent'
  });
  
  const [models, setModels] = useState<Record<string, Model[]>>({});
  const [policies, setPolicies] = useState<RouterPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    fetchConfig();
    fetchModels();
    fetchPolicies();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/config/llm`);
      const data = await response.json();
      setConfig(data);
    } catch (error) {
      console.error('Failed to fetch config:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/config/models`);
      const data = await response.json();
      setModels(data);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    }
  };

  const fetchPolicies = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/config/router-policies`);
      const data = await response.json();
      setPolicies(data.policies || []);
    } catch (error) {
      console.error('Failed to fetch policies:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/config/llm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (!response.ok) {
        throw new Error('Failed to save configuration');
      }
      
      setMessage({ type: 'success', text: 'Configuration saved successfully!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/config/reset`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error('Failed to reset configuration');
      }
      
      await fetchConfig();
      setMessage({ type: 'success', text: 'Configuration reset to defaults!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to reset configuration' });
    }
  };

  if (loading) {
    return <div className="llm-config-panel loading">Loading configuration...</div>;
  }

  const allModels = Object.entries(models).flatMap(([provider, providerModels]) =>
    providerModels.map(model => ({ ...model, provider }))
  );

  return (
    <div className="llm-config-panel">
      <div className="config-header">
        <h3>⚙️ LLM Configuration</h3>
        {onClose && (
          <button className="close-button" onClick={onClose}>✕</button>
        )}
      </div>

      {message && (
        <div className={`config-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="config-body">
        {/* Model Selection */}
        <div className="config-group">
          <label htmlFor="model">Model</label>
          <select
            id="model"
            value={config.model}
            onChange={(e) => setConfig({ ...config, model: e.target.value })}
          >
            {allModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} ({model.provider}) - {(model.context_window / 1000).toFixed(0)}K context
              </option>
            ))}
          </select>
          <span className="config-hint">Select the LLM model to use for code generation</span>
        </div>

        {/* Temperature */}
        <div className="config-group">
          <label htmlFor="temperature">
            Temperature: {config.temperature.toFixed(2)}
          </label>
          <input
            type="range"
            id="temperature"
            min="0"
            max="2"
            step="0.1"
            value={config.temperature}
            onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
          />
          <span className="config-hint">
            Lower = more focused and deterministic, Higher = more creative and random
          </span>
        </div>

        {/* Max Tokens */}
        <div className="config-group">
          <label htmlFor="max_tokens">Max Tokens</label>
          <input
            type="number"
            id="max_tokens"
            min="100"
            max="100000"
            step="100"
            value={config.max_tokens}
            onChange={(e) => setConfig({ ...config, max_tokens: parseInt(e.target.value) })}
          />
          <span className="config-hint">Maximum number of tokens to generate per request</span>
        </div>

        {/* Router Policy */}
        <div className="config-group">
          <label htmlFor="router_policy">Router Policy</label>
          <select
            id="router_policy"
            value={config.router_policy}
            onChange={(e) => setConfig({ ...config, router_policy: e.target.value })}
          >
            {policies.map((policy) => (
              <option key={policy.id} value={policy.id}>
                {policy.name}
              </option>
            ))}
          </select>
          {policies.find(p => p.id === config.router_policy)?.description && (
            <span className="config-hint">
              {policies.find(p => p.id === config.router_policy)?.description}
            </span>
          )}
        </div>

        {/* Provider Override */}
        <div className="config-group">
          <label htmlFor="provider">Provider (Optional)</label>
          <select
            id="provider"
            value={config.provider || ''}
            onChange={(e) => setConfig({ ...config, provider: e.target.value || undefined })}
          >
            <option value="">Auto (from model)</option>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="google">Google</option>
            <option value="emergent">Emergent (Universal Key)</option>
          </select>
          <span className="config-hint">Override provider (usually auto-detected from model)</span>
        </div>
      </div>

      <div className="config-footer">
        <button className="button-secondary" onClick={handleReset}>
          Reset to Defaults
        </button>
        <button
          className="button-primary"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
};

export default LLMConfigPanel;
