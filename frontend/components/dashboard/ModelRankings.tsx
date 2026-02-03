'use client';

import { useEffect, useState } from 'react';
import {
  fetchLatencyLeaderboard,
  fetchSuccessRateLeaderboard,
  fetchPeerReviewLeaderboard,
  LeaderboardEntry,
} from '@/lib/api';

type LeaderboardType = 'latency' | 'success-rate' | 'peer-review';

interface LeaderboardData {
  latency: LeaderboardEntry[];
  'success-rate': LeaderboardEntry[];
  'peer-review': LeaderboardEntry[];
}

export default function ModelRankings() {
  const [activeTab, setActiveTab] = useState<LeaderboardType>('latency');
  const [data, setData] = useState<LeaderboardData>({
    latency: [],
    'success-rate': [],
    'peer-review': [],
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [latencyData, successData, peerReviewData] = await Promise.all([
          fetchLatencyLeaderboard(10).catch(() => ({ leaderboard: [] })),
          fetchSuccessRateLeaderboard(10).catch(() => ({ leaderboard: [] })),
          fetchPeerReviewLeaderboard(10).catch(() => ({ leaderboard: [] })),
        ]);

        setData({
          latency: latencyData.leaderboard,
          'success-rate': successData.leaderboard,
          'peer-review': peerReviewData.leaderboard,
        });
      } catch (error) {
        console.error('Failed to load leaderboards:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const tabs: { id: LeaderboardType; label: string }[] = [
    { id: 'latency', label: 'Speed' },
    { id: 'success-rate', label: 'Reliability' },
    { id: 'peer-review', label: 'Quality' },
  ];

  const currentData = data[activeTab];

  const formatValue = (entry: LeaderboardEntry) => {
    if (activeTab === 'latency') {
      return `${Math.round(entry.metric_value)}ms`;
    } else if (activeTab === 'success-rate') {
      return `${entry.metric_value.toFixed(1)}%`;
    } else {
      return `#${entry.metric_value.toFixed(1)}`;
    }
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) {
      return (
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-yellow-100 text-yellow-800 text-xs font-medium">
          1
        </span>
      );
    } else if (rank === 2) {
      return (
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-200 text-gray-700 text-xs font-medium">
          2
        </span>
      );
    } else if (rank === 3) {
      return (
        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-100 text-orange-700 text-xs font-medium">
          3
        </span>
      );
    }
    return (
      <span className="inline-flex items-center justify-center w-6 h-6 text-gray-500 text-xs">
        {rank}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Model Rankings</h3>
        <p className="text-sm text-gray-500 mt-1">Compare model performance across metrics</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 text-center text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="p-6">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center space-x-4 animate-pulse">
                <div className="w-6 h-6 bg-gray-200 rounded-full"></div>
                <div className="flex-1 h-4 bg-gray-200 rounded"></div>
                <div className="w-16 h-4 bg-gray-200 rounded"></div>
              </div>
            ))}
          </div>
        ) : currentData.length === 0 ? (
          <div className="text-center py-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-500">No data available yet</p>
            <p className="text-xs text-gray-400">Start using the council to see rankings</p>
          </div>
        ) : (
          <div className="space-y-3">
            {currentData.map((entry) => (
              <div
                key={entry.model_id}
                className="flex items-center space-x-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {getRankBadge(entry.rank)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {entry.model_name}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{entry.model_id}</p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-gray-900">
                    {formatValue(entry)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
