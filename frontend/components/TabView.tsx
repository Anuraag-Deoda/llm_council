'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ModelResponse } from '@/lib/api';

interface TabViewProps {
  responses: ModelResponse[];
}

export default function TabView({ responses }: TabViewProps) {
  const [activeTab, setActiveTab] = useState(0);

  if (responses.length === 0) {
    return null;
  }

  const activeResponse = responses[activeTab];

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Tab Headers */}
      <div className="flex border-b border-gray-200 overflow-x-auto bg-gray-50">
        {responses.map((response, index) => (
          <button
            key={response.model_id}
            onClick={() => setActiveTab(index)}
            className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
              activeTab === index
                ? 'bg-white text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            {response.error ? (
              <span className="flex items-center gap-1">
                <span className="text-red-500">⚠</span>
                {response.model_id.split('/').pop()?.split(':')[0] || response.model_id}
              </span>
            ) : (
              response.model_id.split('/').pop()?.split(':')[0] || response.model_id
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-4 bg-white">
        <div className="mb-2 text-xs text-gray-500">
          Model: <span className="font-mono">{activeResponse.model_id}</span>
        </div>

        {activeResponse.error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
            <strong>Error:</strong> {activeResponse.error}
          </div>
        ) : (
          <div className="prose max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {activeResponse.response}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
