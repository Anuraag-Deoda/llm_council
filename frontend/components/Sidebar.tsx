'use client';

import React from 'react';
import { ModelInfo } from '@/lib/api';

export type ChatType = 'council' | 'individual';

export interface Chat {
  id: string;
  type: ChatType;
  name: string;
  modelId?: string; // For individual chats
  lastMessage?: string;
  timestamp?: number;
  unread?: number;
}

interface SidebarProps {
  models: ModelInfo[];
  conversations: Chat[];
  activeChat: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: (type: ChatType, modelId?: string) => void;
}

export default function Sidebar({
  models,
  conversations,
  activeChat,
  onSelectChat,
  onNewChat,
}: SidebarProps) {
  const [showNewChat, setShowNewChat] = React.useState(false);

  return (
    <div className="w-80 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h1 className="text-xl font-bold text-gray-900 mb-1">LLM Council</h1>
        <p className="text-xs text-gray-600">Select a chat or start new</p>
      </div>

      {/* New Chat Button */}
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={() => setShowNewChat(!showNewChat)}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center justify-center gap-2"
        >
          <span>+</span>
          <span>New Chat</span>
        </button>
      </div>

      {/* New Chat Options */}
      {showNewChat && (
        <div className="p-3 border-b border-gray-200 bg-gray-50 space-y-2">
          {/* Council Group */}
          <button
            onClick={() => {
              onNewChat('council');
              setShowNewChat(false);
            }}
            className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm text-left flex items-center gap-3"
          >
            <span className="text-2xl">🏛️</span>
            <div>
              <div className="font-medium text-gray-900">Council Group</div>
              <div className="text-xs text-gray-500">All models collaborate</div>
            </div>
          </button>

          {/* Individual Models */}
          <div className="text-xs font-semibold text-gray-500 uppercase mt-3 mb-2">
            Individual Models
          </div>
          <div className="max-h-60 overflow-y-auto space-y-1">
            {models.map((model) => (
              <button
                key={model.id}
                onClick={() => {
                  onNewChat('individual', model.id);
                  setShowNewChat(false);
                }}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-sm text-left"
              >
                <div className="font-medium text-gray-900 truncate">
                  {model.name}
                </div>
                <div className="text-xs text-gray-500 truncate">{model.provider}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-6 text-center text-gray-500 text-sm">
            No conversations yet.
            <br />
            Click "New Chat" to start!
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {conversations.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
                  activeChat === chat.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0 text-2xl">
                    {chat.type === 'council' ? '🏛️' : '🤖'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-gray-900 truncate">
                      {chat.name}
                    </div>
                    {chat.lastMessage && (
                      <div className="text-sm text-gray-500 truncate">
                        {chat.lastMessage}
                      </div>
                    )}
                    {chat.timestamp && (
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(chat.timestamp).toLocaleString()}
                      </div>
                    )}
                  </div>
                  {chat.unread && chat.unread > 0 && (
                    <div className="flex-shrink-0 bg-blue-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {chat.unread}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
