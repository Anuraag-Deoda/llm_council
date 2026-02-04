'use client';

import { useAuth } from '@/lib/auth-context';
import ProfileCard from '@/components/profile/ProfileCard';
import ConversationHistory from '@/components/profile/ConversationHistory';

export default function ProfilePage() {
  const { user } = useAuth();

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
              Profile
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
            Your Profile
          </h1>
          <p className="mt-2 text-base" style={{ color: 'var(--color-text-secondary)' }}>
            Manage your account and view your activity history.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 animate-slide-up stagger-1">
          {[
            { label: 'Conversations', value: '24', icon: '💬' },
            { label: 'Documents', value: '12', icon: '📄' },
            { label: 'Messages', value: '156', icon: '✉️' },
            { label: 'Member Since', value: user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '--', icon: '📅' },
          ].map((stat, i) => (
            <div
              key={stat.label}
              className="rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
              }}
            >
              <span className="text-2xl mb-2 block">{stat.icon}</span>
              <p className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                {stat.value}
              </p>
              <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Profile Card */}
          <div className="lg:col-span-1 animate-slide-up stagger-2">
            <ProfileCard />
          </div>

          {/* Conversation History */}
          <div className="lg:col-span-2 animate-slide-up stagger-3">
            <ConversationHistory />
          </div>
        </div>
      </div>
    </div>
  );
}
