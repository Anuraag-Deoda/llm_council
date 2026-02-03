'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchConversations, deleteConversation, ConversationHistory as ConvHistory } from '@/lib/api';

export default function ConversationHistory() {
  const [conversations, setConversations] = useState<ConvHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await fetchConversations();
      setConversations(data.sort((a, b) => b.updated_at - a.updated_at));
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this conversation?')) return;

    setDeleteId(id);
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.conversation_id !== id));
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    } finally {
      setDeleteId(null);
    }
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / 86400000);

    if (days === 0) {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
      });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return date.toLocaleDateString('en-US', { weekday: 'long' });
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      });
    }
  };

  const getPreview = (conv: ConvHistory) => {
    if (conv.messages.length === 0) return 'No messages';
    const lastMessage = conv.messages[conv.messages.length - 1];
    return lastMessage.content.length > 100
      ? lastMessage.content.substring(0, 100) + '...'
      : lastMessage.content;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Conversation History</h3>
          <p className="text-sm text-gray-500 mt-1">Your recent conversations with the council</p>
        </div>
        <span className="text-sm text-gray-500">{conversations.length} total</span>
      </div>

      <div className="divide-y divide-gray-200">
        {isLoading ? (
          <div className="p-6 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse flex space-x-4">
                <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              </div>
            ))}
          </div>
        ) : conversations.length === 0 ? (
          <div className="p-12 text-center">
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
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <h3 className="mt-4 text-sm font-medium text-gray-900">No conversations yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Start a new conversation to see it here.
            </p>
            <Link
              href="/chat"
              className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-indigo-600 hover:bg-indigo-700"
            >
              Start chatting
            </Link>
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.conversation_id}
              className="p-4 hover:bg-gray-50 transition-colors flex items-start"
            >
              <div className="flex-shrink-0 mr-4">
                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-indigo-600"
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
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    Conversation {conv.conversation_id.substring(0, 8)}...
                  </p>
                  <span className="text-xs text-gray-500">{formatDate(conv.updated_at)}</span>
                </div>
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">{getPreview(conv)}</p>
                <div className="mt-2 flex items-center space-x-4">
                  <span className="text-xs text-gray-500">
                    {conv.messages.length} message{conv.messages.length !== 1 ? 's' : ''}
                  </span>
                  <Link
                    href={`/chat?conversation=${conv.conversation_id}`}
                    className="text-xs text-indigo-600 hover:text-indigo-500 font-medium"
                  >
                    Continue
                  </Link>
                  <button
                    onClick={() => handleDelete(conv.conversation_id)}
                    disabled={deleteId === conv.conversation_id}
                    className="text-xs text-red-600 hover:text-red-500 font-medium disabled:opacity-50"
                  >
                    {deleteId === conv.conversation_id ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {conversations.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <Link
            href="/chat"
            className="text-sm text-indigo-600 hover:text-indigo-500 font-medium flex items-center justify-center"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Start new conversation
          </Link>
        </div>
      )}
    </div>
  );
}
