'use client';

import { useEffect, useState } from 'react';
import { fetchLeaderboard, LeaderboardEntry } from '@/lib/api';

type RankingType = 'quality' | 'speed' | 'reliability';

export default function ModelRankings() {
  const [rankings, setRankings] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<RankingType>('quality');

  useEffect(() => {
    const loadRankings = async () => {
      setLoading(true);
      try {
        let type: 'peer-review' | 'latency' | 'success-rate' = 'peer-review';
        if (activeTab === 'speed') type = 'latency';
        if (activeTab === 'reliability') type = 'success-rate';

        const data = await fetchLeaderboard(type);
        setRankings(data.slice(0, 6));
      } catch (err) {
        console.error('Failed to fetch rankings:', err);
      } finally {
        setLoading(false);
      }
    };

    loadRankings();
  }, [activeTab]);

  const tabs = [
    { id: 'quality' as RankingType, label: 'Quality' },
    { id: 'speed' as RankingType, label: 'Speed' },
    { id: 'reliability' as RankingType, label: 'Reliability' },
  ];

  const getModelColor = (index: number) => {
    const colors = [
      'var(--gradient-accent)',
      'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
      'var(--gradient-warm)',
      'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
      'linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%)',
      'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
    ];
    return colors[index % colors.length];
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return { icon: '👑', color: '#ffaa00' };
    if (rank === 2) return { icon: '🥈', color: '#c0c0c0' };
    if (rank === 3) return { icon: '🥉', color: '#cd7f32' };
    return { icon: `#${rank}`, color: 'var(--color-text-muted)' };
  };

  const formatValue = (entry: LeaderboardEntry) => {
    if (activeTab === 'quality') {
      return `${(entry.score * 100).toFixed(0)}%`;
    }
    if (activeTab === 'speed') {
      return `${Math.round(entry.score)}ms`;
    }
    return `${(entry.score * 100).toFixed(1)}%`;
  };

  return (
    <div
      className="rounded-2xl overflow-hidden h-full"
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)'
      }}
    >
      {/* Header */}
      <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            Model Rankings
          </h2>
          <button
            className="p-1.5 rounded-lg transition-colors"
            style={{
              background: 'var(--color-bg-tertiary)',
              color: 'var(--color-text-muted)'
            }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div
          className="flex gap-1 p-1 rounded-xl"
          style={{ background: 'var(--color-bg-tertiary)' }}
        >
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className="flex-1 py-2 px-3 text-xs font-medium rounded-lg transition-all duration-200"
              style={{
                background: activeTab === tab.id ? 'var(--color-bg-secondary)' : 'transparent',
                color: activeTab === tab.id ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                boxShadow: activeTab === tab.id ? 'var(--shadow-sm)' : 'none'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Rankings List */}
      <div className="p-4">
        {loading ? (
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="h-14 rounded-xl animate-shimmer"
              />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {rankings.map((entry, index) => {
              const badge = getRankBadge(index + 1);
              return (
                <div
                  key={entry.model_id}
                  className="group flex items-center gap-3 p-3 rounded-xl transition-all duration-200"
                  style={{
                    background: 'var(--color-bg-tertiary)',
                    border: '1px solid transparent'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = 'var(--color-border-hover)';
                    e.currentTarget.style.background = 'var(--color-bg-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'transparent';
                    e.currentTarget.style.background = 'var(--color-bg-tertiary)';
                  }}
                >
                  {/* Rank */}
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold"
                    style={{
                      background: index < 3 ? 'var(--color-bg-hover)' : 'transparent',
                      color: badge.color
                    }}
                  >
                    {index < 3 ? badge.icon : badge.icon}
                  </div>

                  {/* Model Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ background: getModelColor(index) }}
                      />
                      <p
                        className="font-medium text-sm truncate"
                        style={{ color: 'var(--color-text-primary)' }}
                      >
                        {entry.model_id}
                      </p>
                    </div>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-muted)' }}>
                      {entry.total_responses?.toLocaleString() || 0} responses
                    </p>
                  </div>

                  {/* Score */}
                  <div className="text-right">
                    <p
                      className="font-mono text-sm font-semibold"
                      style={{ color: 'var(--color-accent)' }}
                    >
                      {formatValue(entry)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
