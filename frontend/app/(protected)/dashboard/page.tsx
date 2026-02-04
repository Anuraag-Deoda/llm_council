'use client';

import { useAuth } from '@/lib/auth-context';
import StatsCards from '@/components/dashboard/StatsCards';
import ModelRankings from '@/components/dashboard/ModelRankings';
import UsageAnalytics from '@/components/dashboard/UsageAnalytics';
import LiveActivity from '@/components/dashboard/LiveActivity';

export default function DashboardPage() {
  const { user } = useAuth();

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="min-h-screen bg-mesh noise-bg">
      <div className="relative z-10 p-8">
        {/* Header */}
        <div className="mb-10 animate-slide-up">
          <div className="flex items-center gap-3 mb-2">
            <span
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'var(--color-accent-muted)',
                color: 'var(--color-accent)'
              }}
            >
              Dashboard
            </span>
            <span style={{ color: 'var(--color-text-muted)' }}>•</span>
            <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {new Date().toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric'
              })}
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
            {getGreeting()}{user?.display_name ? `, ${user.display_name}` : ''}
          </h1>
          <p className="mt-2 text-base" style={{ color: 'var(--color-text-secondary)' }}>
            Here&apos;s an overview of your LLM Council activity and performance.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="mb-10 animate-slide-up stagger-1">
          <StatsCards />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Usage Analytics - Takes 2 columns */}
          <div className="xl:col-span-2 animate-slide-up stagger-2">
            <UsageAnalytics />
          </div>

          {/* Model Rankings - Takes 1 column */}
          <div className="xl:col-span-1 animate-slide-up stagger-3">
            <ModelRankings />
          </div>
        </div>

        {/* Live Activity */}
        <div className="mt-8 animate-slide-up stagger-4">
          <LiveActivity />
        </div>
      </div>
    </div>
  );
}
