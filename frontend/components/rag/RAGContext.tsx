'use client';

import React, { useState } from 'react';

export interface RAGContextChunk {
  document_title: string;
  source_name: string;
  section_title?: string;
  score: number;
  similarity: number;
}

export interface RAGContextData {
  chunks_retrieved: number;
  sources: string[];
  documents: string[];
  retrieval_time_ms: number;
  top_chunks: RAGContextChunk[];
}

interface RAGContextProps {
  data: RAGContextData;
}

export default function RAGContext({ data }: RAGContextProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-4">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <span className="text-purple-600">Knowledge Base</span>
          <span className="text-sm text-purple-500">
            {data.chunks_retrieved} chunks from {data.sources.length} source(s)
          </span>
          <span className="text-xs text-purple-400">
            ({data.retrieval_time_ms}ms)
          </span>
        </div>
        <button className="text-purple-600 hover:text-purple-800">
          {isExpanded ? 'Hide' : 'Show'} Sources
        </button>
      </div>

      {isExpanded && (
        <div className="mt-3 space-y-2">
          {data.top_chunks.map((chunk, i) => (
            <div
              key={i}
              className="bg-white rounded p-2 border border-purple-100 text-sm"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-purple-700">
                    [{chunk.source_name}]
                  </span>
                  <span className="text-gray-700">{chunk.document_title}</span>
                  {chunk.section_title && (
                    <span className="text-gray-500">- {chunk.section_title}</span>
                  )}
                </div>
                <div className="flex items-center space-x-2 text-xs">
                  <span className="text-purple-600" title="Final score">
                    Score: {(chunk.score * 100).toFixed(0)}%
                  </span>
                  <span className="text-gray-400" title="Similarity">
                    Sim: {(chunk.similarity * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
