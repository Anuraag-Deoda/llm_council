'use client';

import { useEffect, useState } from 'react';

interface ActivityItem {
  id: string;
  type: 'conversation' | 'rag_query' | 'model_response' | 'conflict';
  model?: string;
  message: string;
  timestamp: Date;
}

export default function LiveActivity() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLive, setIsLive] = useState(true);

  // Simulate live activity feed
  useEffect(() => {
    const sampleActivities: ActivityItem[] = [
      {
        id: '1',
        type: 'conversation',
        message: 'New council session started',
        timestamp: new Date(Date.now() - 2 * 60000),
      },
      {
        id: '2',
        type: 'model_response',
        model: 'claude-3-opus',
        message: 'Generated response with 95% confidence',
        timestamp: new Date(Date.now() - 5 * 60000),
      },
      {
        id: '3',
        type: 'rag_query',
        message: 'Retrieved 12 relevant chunks from knowledge base',
        timestamp: new Date(Date.now() - 8 * 60000),
      },
      {
        id: '4',
        type: 'model_response',
        model: 'gpt-4-turbo',
        message: 'Completed peer review evaluation',
        timestamp: new Date(Date.now() - 12 * 60000),
      },
      {
        id: '5',
        type: 'conflict',
        message: 'Conflict detected and auto-resolved',
        timestamp: new Date(Date.now() - 15 * 60000),
      },
    ];

    setActivities(sampleActivities);
  }, []);

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'conversation':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'model_response':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case 'rag_query':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        );
      case 'conflict':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        );
    }
  };

  const getActivityColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'conversation':
        return { bg: 'var(--color-accent-muted)', icon: 'var(--color-accent)' };
      case 'model_response':
        return { bg: 'rgba(168, 85, 247, 0.15)', icon: '#a855f7' };
      case 'rag_query':
        return { bg: 'var(--color-success-muted)', icon: 'var(--color-success)' };
      case 'conflict':
        return { bg: 'var(--color-secondary-muted)', icon: 'var(--color-secondary)' };
    }
  };

  const formatTime = (date: Date) => {
    const diff = Date.now() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border)'
      }}
    >
      {/* Header */}
      <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            Live Activity
          </h2>
          {isLive && (
            <span
              className="flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'var(--color-success-muted)',
                color: 'var(--color-success)'
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: 'var(--color-success)' }} />
              Live
            </span>
          )}
        </div>
        <button
          onClick={() => setIsLive(!isLive)}
          className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200"
          style={{
            background: 'var(--color-bg-tertiary)',
            color: 'var(--color-text-secondary)'
          }}
        >
          {isLive ? 'Pause' : 'Resume'}
        </button>
      </div>

      {/* Activity List */}
      <div className="p-4">
        <div className="space-y-3">
          {activities.map((activity, index) => {
            const colors = getActivityColor(activity.type);
            return (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-xl transition-all duration-200"
                style={{
                  background: 'var(--color-bg-tertiary)',
                  animationDelay: `${index * 50}ms`
                }}
              >
                {/* Icon */}
                <div
                  className="p-2 rounded-lg flex-shrink-0"
                  style={{ background: colors.bg }}
                >
                  <span style={{ color: colors.icon }}>
                    {getActivityIcon(activity.type)}
                  </span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm" style={{ color: 'var(--color-text-primary)' }}>
                    {activity.message}
                  </p>
                  {activity.model && (
                    <span
                      className="inline-flex items-center px-2 py-0.5 mt-1 rounded text-xs font-mono"
                      style={{
                        background: 'var(--color-bg-hover)',
                        color: 'var(--color-text-secondary)'
                      }}
                    >
                      {activity.model}
                    </span>
                  )}
                </div>

                {/* Time */}
                <span className="text-xs flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                  {formatTime(activity.timestamp)}
                </span>
              </div>
            );
          })}
        </div>

        {/* View All Link */}
        <button
          className="w-full mt-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
          style={{
            background: 'var(--color-bg-tertiary)',
            color: 'var(--color-text-secondary)'
          }}
        >
          View all activity
        </button>
      </div>
    </div>
  );
}
