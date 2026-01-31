'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface MessageBubbleProps {
  content: string;
  sender: string; // 'user' or model name
  isUser: boolean;
  timestamp: number;
  modelId?: string;
  avatar?: string;
}

export default function MessageBubble({
  content,
  sender,
  isUser,
  timestamp,
  modelId,
}: MessageBubbleProps) {
  // Get avatar emoji based on model
  const getAvatar = () => {
    if (isUser) return '👤';
    if (modelId?.includes('gpt-5.2')) return '🧠';
    if (modelId?.includes('gpt-4')) return '🤖';
    if (modelId?.includes('claude')) return '🎭';
    if (modelId?.includes('deepseek')) return '🔍';
    if (modelId?.includes('gemini')) return '💎';
    return '🤖';
  };

  return (
    <div className={`flex gap-2 mb-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-lg">
          {getAvatar()}
        </div>
      )}

      {/* Message Container */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-2xl`}>
        {/* Sender Name (for non-user messages) */}
        {!isUser && (
          <div className="text-xs font-semibold text-gray-600 mb-1 px-3">
            {sender}
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-4 py-2 ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm">{content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-p:text-gray-800 prose-a:text-blue-600 prose-code:text-gray-900">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 mt-1 px-3`}>
          {new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-lg">
          👤
        </div>
      )}
    </div>
  );
}
