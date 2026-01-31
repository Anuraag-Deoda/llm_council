'use client';

import React, { useState } from 'react';

interface RankingData {
  modelId: string;
  modelName: string;
  averageRank: number;
  votes: number;
  topRankings: number; // How many times ranked #1
}

interface CouncilSummaryCardProps {
  rankings: Array<{
    reviewer_model: string;
    rankings: Array<{
      model_id: string;
      rank: number;
      reasoning: string;
    }>;
  }>;
  models: Array<{ id: string; name: string }>;
}

export default function CouncilSummaryCard({ rankings, models }: CouncilSummaryCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!rankings || rankings.length === 0) return null;

  // Calculate aggregate rankings
  const rankingMap = new Map<string, { totalRank: number; count: number; topRankings: number }>();

  rankings.forEach((review) => {
    review.rankings.forEach((ranking) => {
      const current = rankingMap.get(ranking.model_id) || { totalRank: 0, count: 0, topRankings: 0 };
      current.totalRank += ranking.rank;
      current.count += 1;
      if (ranking.rank === 1) current.topRankings += 1;
      rankingMap.set(ranking.model_id, current);
    });
  });

  // Convert to array and sort
  const aggregateRankings: RankingData[] = Array.from(rankingMap.entries())
    .map(([modelId, data]) => {
      const modelName = models.find((m) => m.id === modelId)?.name || modelId.split('/').pop()?.split(':')[0] || modelId;
      return {
        modelId,
        modelName,
        averageRank: data.totalRank / data.count,
        votes: data.count,
        topRankings: data.topRankings,
      };
    })
    .sort((a, b) => a.averageRank - b.averageRank);

  const winner = aggregateRankings[0];

  return (
    <div className="my-4 border-2 border-yellow-400 rounded-xl bg-gradient-to-br from-yellow-50 to-orange-50 shadow-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-yellow-100/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-3xl">🏆</span>
          <div className="text-left">
            <h3 className="text-lg font-bold text-gray-900">Peer Review Results</h3>
            <p className="text-sm text-gray-600">
              {rankings.length} councilors reviewed {aggregateRankings.length} responses
            </p>
          </div>
        </div>
        <span className="text-gray-400 text-xl">{isExpanded ? '▼' : '▶'}</span>
      </button>

      {isExpanded && (
        <div className="px-6 pb-6 space-y-4">
          {/* Winner Card */}
          <div className="bg-gradient-to-r from-yellow-400 to-orange-400 rounded-lg p-4 text-white shadow-md">
            <div className="flex items-center gap-3">
              <span className="text-4xl">👑</span>
              <div className="flex-1">
                <div className="text-sm font-semibold opacity-90">Highest Rated Response</div>
                <div className="text-2xl font-bold">{winner.modelName}</div>
                <div className="text-sm opacity-90 mt-1">
                  {winner.topRankings > 0 && (
                    <span>🥇 Ranked #1 by {winner.topRankings} councilor{winner.topRankings > 1 ? 's' : ''}</span>
                  )}
                </div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold">{winner.averageRank.toFixed(1)}</div>
                <div className="text-xs opacity-90">Avg Rank</div>
              </div>
            </div>
          </div>

          {/* Rankings List */}
          <div className="space-y-2">
            {aggregateRankings.map((ranking, index) => (
              <div
                key={ranking.modelId}
                className={`flex items-center gap-3 p-3 rounded-lg border-2 ${
                  index === 0
                    ? 'bg-yellow-100 border-yellow-400'
                    : index === 1
                    ? 'bg-gray-100 border-gray-300'
                    : index === 2
                    ? 'bg-orange-100 border-orange-300'
                    : 'bg-white border-gray-200'
                }`}
              >
                {/* Medal */}
                <div className="text-2xl w-8">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                </div>

                {/* Model Name */}
                <div className="flex-1">
                  <div className="font-semibold text-gray-900">{ranking.modelName}</div>
                  <div className="text-xs text-gray-600">
                    Reviewed by {ranking.votes} councilor{ranking.votes > 1 ? 's' : ''}
                    {ranking.topRankings > 0 && ` • ${ranking.topRankings} top vote${ranking.topRankings > 1 ? 's' : ''}`}
                  </div>
                </div>

                {/* Average Rank */}
                <div className="text-right">
                  <div className="text-xl font-bold text-gray-900">{ranking.averageRank.toFixed(2)}</div>
                  <div className="text-xs text-gray-500">avg rank</div>
                </div>
              </div>
            ))}
          </div>

          {/* Detailed Reviews */}
          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-semibold text-gray-700 hover:text-gray-900 flex items-center gap-2">
              <span>📋</span>
              <span>View detailed reviews</span>
            </summary>
            <div className="mt-3 space-y-3">
              {rankings.map((review, idx) => (
                <div key={idx} className="bg-white rounded-lg p-4 border border-gray-200">
                  <div className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                    <span>👨‍⚖️</span>
                    <span>
                      {models.find((m) => m.id === review.reviewer_model)?.name ||
                        review.reviewer_model.split('/').pop()?.split(':')[0] ||
                        review.reviewer_model}
                    </span>
                  </div>
                  <div className="space-y-2">
                    {review.rankings.map((r, i) => (
                      <div key={i} className="text-sm pl-4 border-l-2 border-gray-300">
                        <div className="font-medium text-gray-900">
                          #{r.rank}:{' '}
                          {models.find((m) => m.id === r.model_id)?.name ||
                            r.model_id.split('/').pop()?.split(':')[0] ||
                            r.model_id}
                        </div>
                        <div className="text-gray-600 text-xs mt-1">{r.reasoning}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
