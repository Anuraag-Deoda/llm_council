'use client';

import React, { useState } from 'react';
import { ModelResponse, ReviewResponse } from '@/lib/api';
import TabView from './TabView';

interface CouncilDeliberationProps {
  firstOpinions: ModelResponse[];
  reviews: ReviewResponse[];
  isComplete: boolean;
}

export default function CouncilDeliberation({
  firstOpinions,
  reviews,
  isComplete,
}: CouncilDeliberationProps) {
  const [isExpanded, setIsExpanded] = useState(!isComplete);

  if (firstOpinions.length === 0) return null;

  return (
    <div className="mb-4 border border-gray-200 rounded-lg bg-white shadow-sm">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-lg">🏛️</span>
          <span className="font-semibold text-gray-900">
            Council Deliberation
          </span>
          <span className="text-xs text-gray-500">
            ({firstOpinions.length} members)
          </span>
        </div>
        <span className="text-gray-400">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* First Opinions */}
          <div>
            <h3 className="font-semibold mb-2 text-sm text-gray-700 flex items-center gap-2">
              <span>💭</span>
              <span>Stage 1: Council Member Responses</span>
            </h3>
            <TabView responses={firstOpinions} />
          </div>

          {/* Reviews */}
          {reviews.length > 0 && (
            <div>
              <h3 className="font-semibold mb-2 text-sm text-gray-700 flex items-center gap-2">
                <span>⚖️</span>
                <span>Stage 2: Peer Reviews</span>
              </h3>
              <div className="space-y-2">
                {reviews.map((review, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-gray-50 rounded border border-gray-200 text-sm"
                  >
                    <div className="font-medium mb-1 text-gray-900">
                      Reviewer: {review.reviewer_model.split('/').pop()?.split(':')[0] ||
                        review.reviewer_model}
                    </div>
                    {review.rankings.length > 0 ? (
                      <div className="text-xs text-gray-600 space-y-1">
                        {review.rankings.map((r, i) => (
                          <div key={i} className="flex items-start gap-2">
                            <span className="font-semibold min-w-[2rem]">
                              #{r.rank}:
                            </span>
                            <div>
                              <span className="font-medium">
                                {r.model_id.split('/').pop()?.split(':')[0] || r.model_id}
                              </span>
                              {' - '}
                              <span>{r.reasoning}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-500 italic">
                        No rankings provided
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
