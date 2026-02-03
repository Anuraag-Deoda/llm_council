'use client';

import { useAuth } from '@/lib/auth-context';
import StatsCards from '@/components/dashboard/StatsCards';
import ModelRankings from '@/components/dashboard/ModelRankings';
import UsageAnalytics from '@/components/dashboard/UsageAnalytics';
import LiveActivity from '@/components/dashboard/LiveActivity';

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.display_name ? `, ${user.display_name}` : ''}!
        </h1>
        <p className="text-gray-600 mt-1">
          Here&apos;s what&apos;s happening with your LLM Council.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="mb-8">
        <StatsCards />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Usage Analytics - Takes 2 columns */}
        <div className="lg:col-span-2">
          <UsageAnalytics />
        </div>

        {/* Model Rankings - Takes 1 column */}
        <div className="lg:col-span-1">
          <ModelRankings />
        </div>
      </div>

      {/* Live Activity */}
      <div className="mt-8">
        <LiveActivity />
      </div>
    </div>
  );
}
