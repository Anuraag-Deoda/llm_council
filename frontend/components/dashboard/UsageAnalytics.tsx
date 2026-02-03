'use client';

import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { fetchUsageTrends, fetchCostTrends, TrendData } from '@/lib/api';

type ChartType = 'usage' | 'cost';

interface ChartData {
  date: string;
  value: number;
  label: string;
}

export default function UsageAnalytics() {
  const [activeChart, setActiveChart] = useState<ChartType>('usage');
  const [usageData, setUsageData] = useState<ChartData[]>([]);
  const [costData, setCostData] = useState<ChartData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [days, setDays] = useState(7);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const [usage, cost] = await Promise.all([
          fetchUsageTrends(days).catch(() => ({ trends: [] })),
          fetchCostTrends(days).catch(() => ({ trends: [] })),
        ]);

        setUsageData(
          usage.trends.map((t: TrendData) => ({
            date: new Date(t.timestamp).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }),
            value: t.value,
            label: t.label,
          }))
        );

        setCostData(
          cost.trends.map((t: TrendData) => ({
            date: new Date(t.timestamp).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }),
            value: t.value,
            label: t.label,
          }))
        );
      } catch (error) {
        console.error('Failed to load trends:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, [days]);

  const chartData = activeChart === 'usage' ? usageData : costData;
  const chartColor = activeChart === 'usage' ? '#6366f1' : '#10b981';
  const chartLabel = activeChart === 'usage' ? 'Conversations' : 'Cost (USD)';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Usage Analytics</h3>
          <p className="text-sm text-gray-500 mt-1">Track usage and costs over time</p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value={7}>7 days</option>
            <option value={14}>14 days</option>
            <option value={30}>30 days</option>
          </select>
        </div>
      </div>

      {/* Chart type toggle */}
      <div className="px-6 pt-4">
        <div className="inline-flex rounded-lg bg-gray-100 p-1">
          <button
            onClick={() => setActiveChart('usage')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activeChart === 'usage'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Usage
          </button>
          <button
            onClick={() => setActiveChart('cost')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
              activeChart === 'cost'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Cost
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="p-6">
        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="h-64 flex items-center justify-center">
            <div className="text-center">
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
                  d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
                />
              </svg>
              <p className="mt-2 text-sm text-gray-500">No data available</p>
              <p className="text-xs text-gray-400">Start using the app to see analytics</p>
            </div>
          </div>
        ) : (
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={chartColor} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={chartColor} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tickFormatter={(value) =>
                    activeChart === 'cost' ? `$${value.toFixed(2)}` : value.toString()
                  }
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '14px',
                  }}
                  formatter={(value: number) => [
                    activeChart === 'cost' ? `$${value.toFixed(2)}` : value,
                    chartLabel,
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke={chartColor}
                  strokeWidth={2}
                  fill="url(#colorValue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
