import React, { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, Check, X, TestTube, Star } from 'lucide-react';
import { aiModelService } from '../services/aiModelService';
import { AIModelConfig, AIModelConfigCreate, AIProvider } from '../types';
import { ApiError } from '../services/apiClient';

const AIModelSettings: React.FC = () => {
  const [models, setModels] = useState<AIModelConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<AIModelConfigCreate>({
    name: '',
    provider: 'gemini',
    api_key: '',
    model_name: '',
    base_url: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<number | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const data = await aiModelService.getAIModels();
      setModels(data);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to load AI models');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingId) {
        await aiModelService.updateAIModel(editingId, formData);
        setSuccess('Model updated successfully');
      } else {
        await aiModelService.createAIModel(formData);
        setSuccess('Model created successfully');
      }
      setShowForm(false);
      setEditingId(null);
      resetForm();
      loadModels();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to save model');
    }
  };

  const handleEdit = (model: AIModelConfig) => {
    setFormData({
      name: model.name,
      provider: model.provider,
      api_key: '', // Don't show existing key
      model_name: model.model_name,
      base_url: model.base_url || ''
    });
    setEditingId(model.id);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this model?')) return;
    
    try {
      await aiModelService.deleteAIModel(id);
      setSuccess('Model deleted successfully');
      loadModels();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to delete model');
    }
  };

  const handleTest = async (id: number) => {
    setTestingId(id);
    try {
      const result = await aiModelService.testAIModel(id);
      if (result.success) {
        setSuccess(`Model connection test successful`);
      } else {
        setError(`Connection test failed: ${result.message}`);
      }
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Connection test failed');
    } finally {
      setTestingId(null);
    }
  };

  const handleSetDefault = async (id: number) => {
    try {
      await aiModelService.setDefaultModel(id);
      setSuccess('Default model updated');
      loadModels();
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError.detail || 'Failed to set default model');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      provider: 'gemini',
      api_key: '',
      model_name: '',
      base_url: ''
    });
  };

  const maskApiKey = (key: string) => {
    if (!key || key.length < 8) return '••••••••';
    return key.substring(0, 4) + '••••••••' + key.substring(key.length - 4);
  };

  if (loading) {
    return <div className="text-slate-400 animate-pulse">Loading AI models...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">AI Model Settings</h2>
        <button
          onClick={() => {
            resetForm();
            setEditingId(null);
            setShowForm(true);
          }}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center gap-2"
        >
          <Plus size={18} /> Add Model
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
          {success}
        </div>
      )}

      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            {editingId ? 'Edit Model' : 'Add New Model'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Provider</label>
              <select
                value={formData.provider}
                onChange={(e) => setFormData({ ...formData, provider: e.target.value as AIProvider })}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
              >
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI</option>
                <option value="claude">Anthropic Claude</option>
                <option value="custom">Custom (OpenAI-compatible)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">API Key</label>
              <input
                type="password"
                value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                placeholder={editingId ? "Leave empty to keep existing key" : "Enter API key"}
                required={!editingId}
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Model Name</label>
              <input
                type="text"
                value={formData.model_name}
                onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                placeholder="e.g., gpt-4, claude-3-opus, gemini-2.0-flash-exp"
                required
              />
            </div>

            {(formData.provider === 'custom' || formData.provider === 'openai') && (
              <div>
                <label className="block text-sm text-slate-400 mb-1">Base URL (Optional)</label>
                <input
                  type="text"
                  value={formData.base_url || ''}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 text-white"
                  placeholder="http://localhost:8000/v1"
                />
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded flex items-center gap-2"
              >
                <Check size={16} /> {editingId ? 'Update' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingId(null);
                  resetForm();
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded flex items-center gap-2"
              >
                <X size={16} /> Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h3 className="text-lg font-semibold text-slate-200">Configured Models</h3>
        </div>
        <div className="divide-y divide-slate-800">
          {models.length === 0 ? (
            <div className="px-6 py-8 text-center text-slate-500">
              No AI models configured. Click "Add Model" to get started.
            </div>
          ) : (
            models.map((model) => (
              <div key={model.id} className="px-6 py-4 hover:bg-slate-800/30 transition-colors">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="font-semibold text-white">{model.name}</h4>
                      {model.is_default && (
                        <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded flex items-center gap-1">
                          <Star size={12} /> Default
                        </span>
                      )}
                      {!model.is_active && (
                        <span className="px-2 py-1 bg-slate-700 text-slate-400 text-xs rounded">
                          Inactive
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-slate-400 space-y-1">
                      <p>Provider: <span className="text-slate-300">{model.provider}</span></p>
                      <p>Model: <span className="text-slate-300">{model.model_name}</span></p>
                      {model.base_url && (
                        <p>Base URL: <span className="text-slate-300 text-xs">{model.base_url}</span></p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {!model.is_default && (
                      <button
                        onClick={() => handleSetDefault(model.id)}
                        className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-emerald-400"
                        title="Set as default"
                      >
                        <Star size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleTest(model.id)}
                      disabled={testingId === model.id}
                      className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-blue-400 disabled:opacity-50"
                      title="Test connection"
                    >
                      <TestTube size={16} />
                    </button>
                    <button
                      onClick={() => handleEdit(model)}
                      className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-yellow-400"
                      title="Edit"
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(model.id)}
                      className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-red-400"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default AIModelSettings;
