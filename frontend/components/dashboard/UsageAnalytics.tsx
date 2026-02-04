'use client';

import { useEffect, useState } from 'react';
import { fetchUsageTrends, UsageTrend } from '@/lib/api';

export default function UsageAnalytics() {
  const [data, setData] = useState<UsageTrend[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('7d');

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
        const trends = await fetchUsageTrends(days);
        setData(trends);
      } catch (err) {
        console.error('Failed to fetch usage trends:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [period]);

  const maxValue = Math.max(...data.map(d => d.count), 1);
  const totalRequests = data.reduce((sum, d) => sum + d.count, 0);
  const avgPerDay = data.length > 0 ? Math.round(totalRequests / data.length) : 0;

  const periods = [
    { id: '7d' as const, label: '7 days' },
    { id: '30d' as const, label: '30 days' },
    { id: '90d' as const, label: '90 days' },
  ];

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
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Usage Analytics
            </h2>
            <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
              Request volume over time
            </p>
          </div>
          <div
            className="flex gap-1 p-1 rounded-xl"
            style={{ background: 'var(--color-bg-tertiary)' }}
          >
            {periods.map((p) => (
              <button
                key={p.id}
                onClick={() => setPeriod(p.id)}
                className="py-1.5 px-3 text-xs font-medium rounded-lg transition-all duration-200"
                style={{
                  background: period === p.id ? 'var(--color-bg-secondary)' : 'transparent',
                  color: period === p.id ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                  boxShadow: period === p.id ? 'var(--shadow-sm)' : 'none'
                }}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex gap-8 mt-6">
          <div>
            <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
              {totalRequests.toLocaleString()}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              Total requests
            </p>
          </div>
          <div>
            <p className="text-2xl font-bold" style={{ color: 'var(--color-accent)' }}>
              {avgPerDay.toLocaleString()}
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
              Daily average
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        {loading ? (
          <div className="h-[200px] animate-shimmer rounded-xl" />
        ) : (
          <div className="h-[200px] flex items-end gap-1">
            {data.map((item, index) => {
              const height = (item.count / maxValue) * 100;
              return (
                <div
                  key={item.date}
                  className="flex-1 group relative"
                >
                  {/* Tooltip */}
                  <div
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 rounded-lg text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-10"
                    style={{
                      background: 'var(--color-bg-elevated)',
                      border: '1px solid var(--color-border)',
                      boxShadow: 'var(--shadow-md)'
                    }}
                  >
                    <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                      {item.count.toLocaleString()} requests
                    </p>
                    <p style={{ color: 'var(--color-text-muted)' }}>
                      {new Date(item.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric'
                      })}
                    </p>
                  </div>

                  {/* Bar */}
                  <div
                    className="w-full rounded-t-md transition-all duration-300 group-hover:opacity-80"
                    style={{
                      height: `${Math.max(height, 4)}%`,
                      background: index === data.length - 1
                        ? 'var(--gradient-accent)'
                        : 'var(--color-accent-muted)',
                      animationDelay: `${index * 30}ms`
                    }}
                  />
                </div>
              );
            })}
          </div>
        )}

        {/* X-axis labels */}
        {!loading && data.length > 0 && (
          <div className="flex justify-between mt-3 px-1">
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {new Date(data[0].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {new Date(data[data.length - 1].date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
