'use client';

import React, { useState, useRef, useEffect } from 'react';
import { streamChat, ModelResponse, ReviewResponse, StreamChunk } from '@/lib/api';
import MessageList, { Message } from './MessageList';
import StageIndicator, { Stage } from './StageIndicator';
import TabView from './TabView';
import ModelSelector from './ModelSelector';

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [selectedModels, setSelectedModels] = useState<string[]>([]);

  // Council state
  const [currentStage, setCurrentStage] = useState<Stage>('idle');
  const [stageMessage, setStageMessage] = useState('');
  const [firstOpinions, setFirstOpinions] = useState<ModelResponse[]>([]);
  const [reviews, setReviews] = useState<ReviewResponse[]>([]);
  const [finalResponse, setFinalResponse] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, finalResponse]);

  const resetCouncilState = () => {
    setCurrentStage('idle');
    setStageMessage('');
    setFirstOpinions([]);
    setReviews([]);
    setFinalResponse('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    // Reset council state for new query
    resetCouncilState();

    try {
      const newConversationId = await streamChat(
        userMessage.content,
        conversationId,
        selectedModels.length > 0 ? selectedModels : null,
        handleStreamChunk
      );

      if (newConversationId && !conversationId) {
        setConversationId(newConversationId);
      }
    } catch (error) {
      console.error('Error streaming chat:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.',
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleStreamChunk = (chunk: StreamChunk) => {
    switch (chunk.type) {
      case 'stage_update':
        if (chunk.stage) {
          setCurrentStage(chunk.stage as Stage);
        }
        if (chunk.content) {
          setStageMessage(chunk.content);
        }
        break;

      case 'model_response':
        if (chunk.model_id && chunk.content) {
          setFirstOpinions((prev) => {
            // Check if this model already has a response
            const existing = prev.find((r) => r.model_id === chunk.model_id);
            if (existing) {
              return prev;
            }

            return [
              ...prev,
              {
                model_id: chunk.model_id,
                response: chunk.content || '',
                timestamp: Date.now(),
              },
            ];
          });
        }
        break;

      case 'review':
        if (chunk.model_id && chunk.data) {
          setReviews((prev) => [
            ...prev,
            {
              reviewer_model: chunk.model_id,
              rankings: chunk.data.rankings || [],
              timestamp: Date.now(),
            },
          ]);
        }
        break;

      case 'final_response':
        if (chunk.content) {
          setFinalResponse((prev) => prev + chunk.content);
        }
        break;

      case 'complete':
        // Add the final response as an assistant message
        if (finalResponse) {
          const assistantMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: finalResponse,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
        }
        setCurrentStage('complete');
        break;

      case 'error':
        console.error('Stream error:', chunk.content);
        break;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    resetCouncilState();
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LLM Council</h1>
            <p className="text-sm text-gray-600">
              Collective intelligence from multiple AI models
            </p>
          </div>
          <button
            onClick={startNewConversation}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            New Conversation
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto px-6 py-4">
        <div className="max-w-6xl mx-auto">
          {/* Model Selector */}
          <ModelSelector
            selectedModels={selectedModels}
            onModelSelectionChange={setSelectedModels}
          />

          {/* Messages */}
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-96">
              <div className="text-center">
                <h2 className="text-3xl font-bold text-gray-300 mb-2">🏛️</h2>
                <p className="text-gray-500">
                  Ask a question to convene the LLM Council
                </p>
              </div>
            </div>
          ) : (
            <MessageList messages={messages} messagesEndRef={messagesEndRef} />
          )}

          {/* Council Deliberation UI */}
          {loading && (
            <div className="mt-6 p-6 bg-white rounded-lg shadow-sm border border-gray-200">
              <StageIndicator currentStage={currentStage} stageMessage={stageMessage} />

              {/* First Opinions Tab View */}
              {firstOpinions.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold mb-2 text-sm text-gray-700">
                    Council Member Responses
                  </h3>
                  <TabView responses={firstOpinions} />
                </div>
              )}

              {/* Reviews */}
              {reviews.length > 0 && (
                <div className="mb-4">
                  <h3 className="font-semibold mb-2 text-sm text-gray-700">
                    Peer Reviews
                  </h3>
                  <div className="space-y-2">
                    {reviews.map((review) => (
                      <div
                        key={review.reviewer_model}
                        className="p-3 bg-gray-50 rounded border border-gray-200 text-sm"
                      >
                        <div className="font-medium mb-1">
                          {review.reviewer_model.split('/').pop()?.split(':')[0] ||
                            review.reviewer_model}
                        </div>
                        <div className="text-xs text-gray-600">
                          {review.rankings.map((r, i) => (
                            <div key={i}>
                              #{r.rank}:{' '}
                              {r.model_id.split('/').pop()?.split(':')[0] || r.model_id} -{' '}
                              {r.reasoning}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Final Response (Streaming) */}
              {finalResponse && (
                <div className="mb-4">
                  <h3 className="font-semibold mb-2 text-sm text-gray-700">
                    Chairman's Final Response
                  </h3>
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded border border-blue-200">
                    <div className="prose prose-sm max-w-none">
                      {finalResponse}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Input Area */}
      <footer className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="max-w-6xl mx-auto">
          <div className="flex gap-3">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask the LLM Council a question..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {loading ? 'Thinking...' : 'Send'}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </p>
        </form>
      </footer>
    </div>
  );
}
