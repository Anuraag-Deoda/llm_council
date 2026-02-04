'use client';

import { useEffect, useState } from 'react';
import { fetchAnalyticsSummary, AnalyticsSummary } from '@/lib/api';

export default function StatsCards() {
  const [stats, setStats] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await fetchAnalyticsSummary();
        setStats(data);
      } catch (err) {
        console.error('Failed to fetch stats:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  const cards = [
    {
      title: 'Total Conversations',
      value: stats?.total_conversations || 0,
      change: '+12%',
      changeType: 'positive' as const,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #00d4ff 0%, #00ff88 100%)',
    },
    {
      title: 'Active Models',
      value: stats?.active_models || 0,
      change: 'All operational',
      changeType: 'neutral' as const,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
    },
    {
      title: 'Avg Latency',
      value: stats?.avg_latency_ms ? `${Math.round(stats.avg_latency_ms)}ms` : '--',
      change: '-8%',
      changeType: 'positive' as const,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #ffaa00 0%, #ff6644 100%)',
    },
    {
      title: 'Success Rate',
      value: stats?.success_rate ? `${(stats.success_rate * 100).toFixed(1)}%` : '--',
      change: 'Excellent',
      changeType: 'positive' as const,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #00ff88 0%, #00d4ff 100%)',
    },
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="rounded-2xl p-6 animate-shimmer"
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              height: '140px'
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
      {cards.map((card, index) => (
        <div
          key={card.title}
          className="group rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1"
          style={{
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            animationDelay: `${index * 100}ms`
          }}
        >
          <div className="flex items-start justify-between mb-4">
            <div
              className="p-2.5 rounded-xl transition-transform duration-300 group-hover:scale-110"
              style={{ background: card.gradient }}
            >
              <span style={{ color: 'var(--color-bg-primary)' }}>
                {card.icon}
              </span>
            </div>
            <span
              className="text-xs font-medium px-2 py-1 rounded-full"
              style={{
                background: card.changeType === 'positive'
                  ? 'var(--color-success-muted)'
                  : 'var(--color-bg-tertiary)',
                color: card.changeType === 'positive'
                  ? 'var(--color-success)'
                  : 'var(--color-text-muted)'
              }}
            >
              {card.change}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium mb-1" style={{ color: 'var(--color-text-muted)' }}>
              {card.title}
            </p>
            <p className="text-2xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
              {typeof card.value === 'number' ? card.value.toLocaleString() : card.value}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
