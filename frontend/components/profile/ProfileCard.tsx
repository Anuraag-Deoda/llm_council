'use client';

import { useAuth } from '@/lib/auth-context';
import Link from 'next/link';

export default function ProfileCard() {
  const { user } = useAuth();

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)'
      }}
    >
      {/* Header Background */}
      <div
        className="h-24 relative"
        style={{
          background: 'var(--gradient-accent)',
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.3) 100%)'
          }}
        />
      </div>

      {/* Avatar */}
      <div className="px-6 -mt-12 relative z-10">
        {user?.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.display_name || 'Profile'}
            className="w-24 h-24 rounded-2xl object-cover"
            style={{
              border: '4px solid var(--color-bg-secondary)',
              boxShadow: 'var(--shadow-lg)'
            }}
          />
        ) : (
          <div
            className="w-24 h-24 rounded-2xl flex items-center justify-center"
            style={{
              background: 'var(--gradient-accent)',
              border: '4px solid var(--color-bg-secondary)',
              boxShadow: 'var(--shadow-lg)'
            }}
          >
            <span className="text-3xl font-bold" style={{ color: 'var(--color-bg-primary)' }}>
              {(user?.display_name || user?.email || '?')[0].toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* User Info */}
      <div className="p-6 pt-4">
        <div className="mb-4">
          <h2 className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {user?.display_name || 'User'}
          </h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
            {user?.email}
          </p>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap gap-2 mb-6">
          <span
            className="px-3 py-1 rounded-full text-xs font-medium"
            style={{
              background: user?.email_verified ? 'var(--color-success-muted)' : 'var(--color-secondary-muted)',
              color: user?.email_verified ? 'var(--color-success)' : 'var(--color-secondary)'
            }}
          >
            {user?.email_verified ? 'Verified' : 'Unverified'}
          </span>
          {user?.has_password && (
            <span
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'var(--color-accent-muted)',
                color: 'var(--color-accent)'
              }}
            >
              Password Set
            </span>
          )}
        </div>

        {/* Account Details */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center justify-between py-2 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Member since</span>
            <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('en-US', {
                    month: 'long',
                    day: 'numeric',
                    year: 'numeric'
                  })
                : '--'}
            </span>
          </div>
          <div className="flex items-center justify-between py-2 border-b" style={{ borderColor: 'var(--color-border)' }}>
            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Last login</span>
            <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
              {user?.last_login_at
                ? new Date(user.last_login_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit'
                  })
                : '--'}
            </span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Account status</span>
            <span
              className="text-sm font-medium flex items-center gap-1.5"
              style={{ color: user?.is_active ? 'var(--color-success)' : 'var(--color-error)' }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: user?.is_active ? 'var(--color-success)' : 'var(--color-error)' }}
              />
              {user?.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          <Link
            href="/settings"
            className="w-full py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all duration-200"
            style={{
              background: 'var(--gradient-accent)',
              color: 'var(--color-bg-primary)',
            }}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Manage Settings
          </Link>
        </div>
      </div>
    </div>
  );
}
