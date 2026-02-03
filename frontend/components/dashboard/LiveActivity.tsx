'use client';

import { useEffect, useState } from 'react';
import { fetchConversations, ConversationHistory } from '@/lib/api';

interface ActivityItem {
  id: string;
  type: 'conversation';
  title: string;
  description: string;
  timestamp: Date;
}

export default function LiveActivity() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadActivity() {
      try {
        const conversations = await fetchConversations().catch(() => []);

        // Convert conversations to activity items and sort by most recent
        const items: ActivityItem[] = conversations
          .map((conv: ConversationHistory) => ({
            id: conv.conversation_id,
            type: 'conversation' as const,
            title: `Conversation ${conv.conversation_id.substring(0, 8)}...`,
            description: `${conv.messages.length} messages`,
            timestamp: new Date(conv.updated_at * 1000),
          }))
          .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
          .slice(0, 10);

        setActivities(items);
      } catch (error) {
        console.error('Failed to load activity:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadActivity();

    // Refresh every 30 seconds
    const interval = setInterval(loadActivity, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
          <p className="text-sm text-gray-500 mt-1">Latest conversations and interactions</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>

      <div className="p-6">
        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-start space-x-3 animate-pulse">
                <div className="w-8 h-8 bg-gray-200 rounded-full"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : activities.length === 0 ? (
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
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-500">No recent activity</p>
            <p className="text-xs text-gray-400">Start a conversation to see activity here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                    <svg
                      className="w-4 h-4 text-indigo-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{activity.title}</p>
                  <p className="text-xs text-gray-500">{activity.description}</p>
                </div>
                <div className="flex-shrink-0">
                  <span className="text-xs text-gray-400">{formatTime(activity.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
