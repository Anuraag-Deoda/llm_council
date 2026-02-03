'use client';

import React, { useState } from 'react';

export interface ConflictSource {
  name: string;
  author: string | null;
  content_preview: string;
}

export interface Conflict {
  type: string;
  confidence: number;
  source_a: ConflictSource;
  source_b: ConflictSource;
  explanation: string;
  recommendation: string;
}

export interface ConflictData {
  conflicts: Conflict[];
}

interface ConflictAlertProps {
  data: ConflictData;
}

const conflictTypeColors: Record<string, string> = {
  factual: 'bg-red-100 text-red-800',
  temporal: 'bg-orange-100 text-orange-800',
  opinion: 'bg-blue-100 text-blue-800',
  numerical: 'bg-yellow-100 text-yellow-800',
  procedural: 'bg-purple-100 text-purple-800',
};

export default function ConflictAlert({ data }: ConflictAlertProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (data.conflicts.length === 0) return null;

  return (
    <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4 mb-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <span className="text-yellow-600 text-lg">Warning</span>
          <span className="font-medium text-yellow-800">
            {data.conflicts.length} Conflict{data.conflicts.length > 1 ? 's' : ''} Detected
          </span>
        </div>
        <button className="text-yellow-700 hover:text-yellow-900">
          {isExpanded ? 'Hide' : 'Show'} Details
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-4">
          {data.conflicts.map((conflict, i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-yellow-200 p-4"
            >
              {/* Conflict header */}
              <div className="flex items-center justify-between mb-3">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium uppercase ${
                    conflictTypeColors[conflict.type] || 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {conflict.type}
                </span>
                <span className="text-sm text-gray-500">
                  Confidence: {(conflict.confidence * 100).toFixed(0)}%
                </span>
              </div>

              {/* Sources */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
                {/* Source A */}
                <div className="bg-red-50 rounded p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-red-600 font-medium">Source A:</span>
                    <span className="text-sm text-gray-700">{conflict.source_a.name}</span>
                  </div>
                  {conflict.source_a.author && (
                    <p className="text-xs text-gray-500 mb-1">
                      by {conflict.source_a.author}
                    </p>
                  )}
                  <p className="text-sm text-gray-700 italic">
                    "{conflict.source_a.content_preview}"
                  </p>
                </div>

                {/* Source B */}
                <div className="bg-blue-50 rounded p-3">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-blue-600 font-medium">Source B:</span>
                    <span className="text-sm text-gray-700">{conflict.source_b.name}</span>
                  </div>
                  {conflict.source_b.author && (
                    <p className="text-xs text-gray-500 mb-1">
                      by {conflict.source_b.author}
                    </p>
                  )}
                  <p className="text-sm text-gray-700 italic">
                    "{conflict.source_b.content_preview}"
                  </p>
                </div>
              </div>

              {/* Explanation */}
              <div className="mb-2">
                <span className="text-sm font-medium text-gray-700">Analysis: </span>
                <span className="text-sm text-gray-600">{conflict.explanation}</span>
              </div>

              {/* Recommendation */}
              <div className="bg-gray-50 rounded p-2">
                <span className="text-sm font-medium text-gray-700">Recommendation: </span>
                <span className="text-sm text-gray-600">{conflict.recommendation}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
