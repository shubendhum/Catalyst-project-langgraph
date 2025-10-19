import React, { useState, useEffect } from 'react';
import { TrendingDown, DollarSign, Zap, BarChart3, PieChart, RefreshCw, Home, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

const CostVisualization = () => {
  const [costStats, setCostStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCostStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/logs/cost-stats`);
      const data = await response.json();
      
      if (data.success) {
        setCostStats(data);
      } else {
        setError(data.error || 'Failed to fetch cost statistics');
      }
    } catch (err) {
      setError('Failed to connect to backend: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCostStats();
    // Refresh every 30 seconds
    const interval = setInterval(fetchCostStats, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !costStats) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  if (!costStats) return null;

  const { global_stats, optimizer_stats } = costStats;

  // Calculate estimated savings from cache hits
  const avgCostPerCall = global_stats.average_cost_per_task / (global_stats.total_llm_calls / global_stats.total_tasks || 1);
  const estimatedSavings = global_stats.total_cache_hits * avgCostPerCall;
  const savingsPercentage = ((estimatedSavings / (global_stats.total_cost + estimatedSavings)) * 100).toFixed(1);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Navigation */}
        <div className="mb-4 flex items-center gap-4">
          <Link 
            to="/" 
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <Home className="w-5 h-5" />
            <span>Chat</span>
          </Link>
          <span className="text-gray-400">/</span>
          <Link 
            to="/logs" 
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <FileText className="w-5 h-5" />
            <span>Backend Logs</span>
          </Link>
        </div>

        <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cost Optimization Dashboard</h2>
          <p className="text-gray-600 text-sm mt-1">Real-time LLM cost tracking and savings</p>
        </div>
        <button
          onClick={fetchCostStats}
          disabled={loading}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className={`w-5 h-5 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Cost */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 text-blue-600" />
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
              TOTAL
            </span>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-gray-900">
              ${global_stats.total_cost.toFixed(4)}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Total LLM Cost
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {global_stats.total_tasks} tasks completed
            </p>
          </div>
        </div>

        {/* Cache Hit Rate */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-8 h-8 text-green-600" />
            <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
              CACHE
            </span>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-gray-900">
              {global_stats.cache_hit_rate.toFixed(1)}%
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Cache Hit Rate
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {global_stats.total_cache_hits.toLocaleString()} / {global_stats.total_llm_calls.toLocaleString()} calls cached
            </p>
          </div>
        </div>

        {/* Estimated Savings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <TrendingDown className="w-8 h-8 text-purple-600" />
            <span className="text-xs font-medium text-purple-700 bg-purple-100 px-2 py-1 rounded">
              SAVED
            </span>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-gray-900">
              ${estimatedSavings.toFixed(4)}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Cost Saved (est.)
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ~{savingsPercentage}% savings from caching
            </p>
          </div>
        </div>

        {/* Average Cost per Task */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="w-8 h-8 text-orange-600" />
            <span className="text-xs font-medium text-orange-700 bg-orange-100 px-2 py-1 rounded">
              AVG
            </span>
          </div>
          <div className="mt-2">
            <div className="text-3xl font-bold text-gray-900">
              ${global_stats.average_cost_per_task.toFixed(4)}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              Avg Cost per Task
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ~{(global_stats.total_llm_calls / global_stats.total_tasks).toFixed(1)} LLM calls/task
            </p>
          </div>
        </div>
      </div>

      {/* Cache Performance Details */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <PieChart className="w-5 h-5 text-blue-600" />
          Cache Performance
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Cache Size */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Cache Size</div>
            <div className="text-2xl font-bold text-gray-900">
              {optimizer_stats?.cache_size || 0}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              cached responses
            </div>
          </div>

          {/* Total Calls */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Total LLM Calls</div>
            <div className="text-2xl font-bold text-gray-900">
              {global_stats.total_llm_calls.toLocaleString()}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              across all tasks
            </div>
          </div>

          {/* Cache Efficiency */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm text-gray-600 mb-1">Cache Efficiency</div>
            <div className="text-2xl font-bold text-gray-900">
              {global_stats.total_cache_hits > 0 
                ? ((global_stats.total_cache_hits / (global_stats.total_llm_calls || 1)) * 100).toFixed(1) 
                : 0}%
            </div>
            <div className="text-xs text-gray-500 mt-1">
              of calls served from cache
            </div>
          </div>
        </div>

        {/* Visual Progress Bar */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-sm mb-2">
            <span className="text-gray-600">Cache Hit Rate Progress</span>
            <span className="font-semibold text-gray-900">
              {global_stats.cache_hit_rate.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-gradient-to-r from-green-500 to-green-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(global_stats.cache_hit_rate, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>
      </div>

      {/* Optimization Insights */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">💡 Optimization Insights</h3>
        <div className="space-y-2">
          {global_stats.cache_hit_rate >= 30 ? (
            <div className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <p className="text-sm text-gray-700">
                Excellent cache performance! Your cache hit rate of {global_stats.cache_hit_rate.toFixed(1)}% 
                is saving significant costs on repeated queries.
              </p>
            </div>
          ) : (
            <div className="flex items-start gap-2">
              <span className="text-yellow-600 font-bold">!</span>
              <p className="text-sm text-gray-700">
                Cache hit rate is at {global_stats.cache_hit_rate.toFixed(1)}%. 
                Similar queries could benefit more from caching.
              </p>
            </div>
          )}
          
          <div className="flex items-start gap-2">
            <span className="text-blue-600 font-bold">→</span>
            <p className="text-sm text-gray-700">
              Average cost per task: ${global_stats.average_cost_per_task.toFixed(4)}. 
              Using OptimizedLLMClient ensures cost-effective model selection.
            </p>
          </div>
          
          {estimatedSavings > 0.01 && (
            <div className="flex items-start gap-2">
              <span className="text-purple-600 font-bold">$</span>
              <p className="text-sm text-gray-700">
                You've saved approximately ${estimatedSavings.toFixed(4)} through intelligent caching, 
                reducing overall spending by ~{savingsPercentage}%.
              </p>
            </div>
          )}
        </div>
      </div>
        </div>
      </div>
    </div>
  );
};

export default CostVisualization;
