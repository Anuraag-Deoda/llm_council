'use client';

import React, { useState, useEffect } from 'react';
import { ModelInfo, fetchModels } from '@/lib/api';

interface ModelSelectorProps {
  selectedModels: string[];
  onModelSelectionChange: (models: string[]) => void;
}

export default function ModelSelector({
  selectedModels,
  onModelSelectionChange,
}: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const fetchedModels = await fetchModels();
      setModels(fetchedModels);

      // If no models selected, select all by default
      if (selectedModels.length === 0) {
        onModelSelectionChange(fetchedModels.map((m) => m.id));
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleModel = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      onModelSelectionChange(selectedModels.filter((id) => id !== modelId));
    } else {
      onModelSelectionChange([...selectedModels, modelId]);
    }
  };

  const selectAll = () => {
    onModelSelectionChange(models.map((m) => m.id));
  };

  const deselectAll = () => {
    onModelSelectionChange([]);
  };

  const groupedModels = {
    openai: models.filter((m) => m.provider === 'openai'),
    openrouter: models.filter((m) => m.provider === 'openrouter'),
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading models...</div>;
  }

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium transition-colors"
      >
        <span>🤖</span>
        <span>
          Council Members ({selectedModels.length}/{models.length})
        </span>
        <span className="ml-auto">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg shadow-lg">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-sm">Select Council Members</h3>
            <div className="flex gap-2">
              <button
                onClick={selectAll}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="text-xs text-gray-600 hover:text-gray-800"
              >
                Deselect All
              </button>
            </div>
          </div>

          {/* OpenAI Models */}
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
              OpenAI Models
            </h4>
            <div className="space-y-2">
              {groupedModels.openai.map((model) => (
                <label
                  key={model.id}
                  className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.id)}
                    onChange={() => toggleModel(model.id)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium">
                      {model.name}
                      {model.is_chairman && (
                        <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                          Chairman
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 font-mono">{model.id}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* OpenRouter Free Models */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">
              OpenRouter Free Models
            </h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {groupedModels.openrouter.map((model) => (
                <label
                  key={model.id}
                  className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(model.id)}
                    onChange={() => toggleModel(model.id)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <div className="text-sm font-medium">{model.name}</div>
                    <div className="text-xs text-gray-500 font-mono">{model.id}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
