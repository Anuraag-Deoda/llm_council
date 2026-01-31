'use client';

import React, { useState } from 'react';
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
  const [isExpanded, setIsExpanded] = useState(false);

  // Get avatar emoji based on model
  const getAvatar = () => {
    if (isUser) return '👤';
    if (modelId?.includes('gpt-5.2')) return '🧠';
    if (modelId?.includes('gpt-4')) return '🤖';
    if (modelId?.includes('claude')) return '🎭';
    if (modelId?.includes('deepseek')) return '🔍';
    if (modelId?.includes('gemini')) return '💎';
    if (modelId?.includes('chairman')) return '👑';
    return '🤖';
  };

  // Check if content is long
  const isLongContent = content.length > 500;
  const displayContent = isLongContent && !isExpanded ? content.substring(0, 500) + '...' : content;

  return (
    <div className={`flex gap-3 mb-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-xl shadow-md">
          {getAvatar()}
        </div>
      )}

      {/* Message Container */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-3xl min-w-[200px]`}>
        {/* Sender Name (for non-user messages) */}
        {!isUser && (
          <div className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-1 px-4">
            {sender}
          </div>
        )}

        {/* Message Bubble */}
        <div
          className={`rounded-2xl px-5 py-3 shadow-md ${
            isUser
              ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-tr-sm'
              : modelId?.includes('chairman')
              ? 'bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/30 dark:to-orange-900/30 text-gray-900 dark:text-gray-100 border-2 border-yellow-400 dark:border-yellow-600 rounded-tl-sm'
              : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-tl-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap text-sm leading-relaxed">{content}</p>
          ) : (
            <div className={`prose prose-sm max-w-none ${
              modelId?.includes('chairman')
                ? 'prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-p:text-gray-800 dark:prose-p:text-gray-200 prose-strong:text-gray-900 dark:prose-strong:text-gray-100'
                : 'prose-headings:text-gray-900 dark:prose-headings:text-gray-100 prose-p:text-gray-700 dark:prose-p:text-gray-300'
            } prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-code:text-gray-900 dark:prose-code:text-gray-100 prose-code:bg-gray-100 dark:prose-code:bg-gray-700 prose-code:px-1 prose-code:py-0.5 prose-code:rounded`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {displayContent}
              </ReactMarkdown>
            </div>
          )}

          {/* Expand/Collapse for long messages */}
          {isLongContent && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className={`text-xs font-semibold mt-2 underline ${
                isUser ? 'text-blue-100 hover:text-white' : 'text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300'
              }`}
            >
              {isExpanded ? 'Show less' : 'Read more'}
            </button>
          )}
        </div>

        {/* Timestamp */}
        <div className={`text-xs text-gray-400 dark:text-gray-500 mt-1 px-4`}>
          {new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-xl shadow-md">
          👤
        </div>
      )}
    </div>
  );
}
