'use client';

import React, { useState } from 'react';
import { ModelInfo } from '@/lib/api';
import { useTheme } from './ThemeProvider';
import { useToast } from './Toast';

export type ChatType = 'council' | 'individual';

export interface Chat {
  id: string;
  type: ChatType;
  name: string;
  modelId?: string;
  lastMessage?: string;
  timestamp?: number;
  unread?: number;
}

interface AdvancedSidebarProps {
  models: ModelInfo[];
  conversations: Chat[];
  activeChat: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: (type: ChatType, modelId?: string) => void;
  onDeleteChat: (chatId: string) => void;
  onClearAll: () => void;
  isOpen: boolean;
  onToggle: () => void;
}

export default function AdvancedSidebar({
  models,
  conversations,
  activeChat,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onClearAll,
  isOpen,
  onToggle,
}: AdvancedSidebarProps) {
  const [showNewChat, setShowNewChat] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { theme, toggleTheme } = useTheme();
  const { showToast } = useToast();

  const filteredConversations = conversations.filter((chat) =>
    chat.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.lastMessage?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleClearAll = () => {
    if (confirm('Clear all conversations? This cannot be undone.')) {
      onClearAll();
      showToast('All conversations cleared', 'success');
    }
  };

  const handleDelete = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      onDeleteChat(chatId);
      showToast('Conversation deleted', 'success');
    }
  };

  const handleExport = () => {
    const data = JSON.stringify(conversations, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm-council-history-${Date.now()}.json`;
    a.click();
    showToast('Chat history exported', 'success');
  };

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:translate-x-0 fixed lg:relative z-50 w-80 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col h-full transition-transform duration-300`}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-500 to-purple-600">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-bold text-white">LLM Council</h1>
            <button
              onClick={onToggle}
              className="lg:hidden text-white hover:bg-white/20 p-2 rounded-lg"
            >
              ✕
            </button>
          </div>
          <p className="text-xs text-white/80">Collective AI Intelligence</p>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b border-gray-200 dark:border-gray-700">
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
          />
        </div>

        {/* Action Buttons */}
        <div className="p-3 border-b border-gray-200 dark:border-gray-700 space-y-2">
          <button
            onClick={() => setShowNewChat(!showNewChat)}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium flex items-center justify-center gap-2"
          >
            <span>+</span>
            <span>New Chat</span>
          </button>

          <div className="flex gap-2">
            <button
              onClick={toggleTheme}
              className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-900 dark:text-white rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
              title="Toggle theme"
            >
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-900 dark:text-white rounded-lg transition-colors text-sm flex items-center justify-center gap-2"
              title="Settings"
            >
              ⚙️
            </button>
          </div>
        </div>

        {/* New Chat Options */}
        {showNewChat && (
          <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 space-y-2 max-h-96 overflow-y-auto">
            {/* Council Group */}
            <button
              onClick={() => {
                onNewChat('council');
                setShowNewChat(false);
              }}
              className="w-full px-3 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm text-left flex items-center gap-3"
            >
              <span className="text-2xl">🏛️</span>
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Council Group</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  All {models.length} models collaborate
                </div>
              </div>
            </button>

            {/* Individual Models */}
            <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mt-3 mb-2">
              Individual Models
            </div>
            <div className="space-y-1">
              {models.map((model) => (
                <button
                  key={model.id}
                  onClick={() => {
                    onNewChat('individual', model.id);
                    setShowNewChat(false);
                  }}
                  className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm text-left"
                >
                  <div className="font-medium text-gray-900 dark:text-white truncate">
                    {model.name}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {model.provider}
                    {model.is_chairman && ' • Chairman'}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Settings Panel */}
        {showSettings && (
          <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 space-y-2">
            <button
              onClick={handleExport}
              className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-sm text-left flex items-center gap-2 text-gray-900 dark:text-white"
            >
              <span>📥</span>
              <span>Export All Conversations</span>
            </button>
            <button
              onClick={handleClearAll}
              className="w-full px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 transition-colors text-sm text-left flex items-center gap-2 text-red-700 dark:text-red-400"
            >
              <span>🗑️</span>
              <span>Clear All Conversations</span>
            </button>
          </div>
        )}

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {filteredConversations.length === 0 ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400 text-sm">
              {searchQuery ? (
                <>
                  No conversations found
                  <br />
                  matching "{searchQuery}"
                </>
              ) : (
                <>
                  No conversations yet.
                  <br />
                  Click "New Chat" to start!
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredConversations.map((chat) => (
                <div
                  key={chat.id}
                  className={`group relative hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                    activeChat === chat.id
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-600'
                      : ''
                  }`}
                >
                  <button
                    onClick={() => onSelectChat(chat.id)}
                    className="w-full px-4 py-3 text-left flex items-center gap-3"
                  >
                    <div className="flex-shrink-0 text-2xl">
                      {chat.type === 'council' ? '🏛️' : '🤖'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 dark:text-white truncate">
                        {chat.name}
                      </div>
                      {chat.lastMessage && (
                        <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                          {chat.lastMessage}
                        </div>
                      )}
                      {chat.timestamp && (
                        <div className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {new Date(chat.timestamp).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                    {chat.unread && chat.unread > 0 && (
                      <div className="flex-shrink-0 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                        {chat.unread}
                      </div>
                    )}
                  </button>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => handleDelete(chat.id, e)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-2 text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-all"
                    title="Delete conversation"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="text-xs text-center text-gray-500 dark:text-gray-400">
            <div className="font-semibold mb-1">Keyboard Shortcuts</div>
            <div className="space-y-0.5">
              <div>
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Ctrl</kbd> +{' '}
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">N</kbd> New
                Chat
              </div>
              <div>
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">Ctrl</kbd> +{' '}
                <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">B</kbd> Toggle
                Sidebar
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
