'use client';

import React, { useState, useRef, useEffect } from 'react';
import { streamChat, streamIndividualChat, ModelInfo, fetchModels, ModelResponse, ReviewResponse, StreamChunk } from '@/lib/api';
import AdvancedSidebar, { Chat, ChatType } from './AdvancedSidebar';
import MessageBubble from './MessageBubble';
import StageIndicator, { Stage } from './StageIndicator';
import CouncilSummaryCard from './CouncilSummaryCard';
import { ToastProvider, useToast } from './Toast';

interface Message {
  id: string;
  content: string;
  sender: string; // 'user' or model name
  isUser: boolean;
  timestamp: number;
  modelId?: string;
}

interface CouncilState {
  stage: Stage;
  stageMessage: string;
  responses: Array<{
    modelId: string;
    content: string;
    timestamp: number;
  }>;
  reviews: Array<{
    reviewer_model: string;
    rankings: Array<{
      model_id: string;
      rank: number;
      reasoning: string;
    }>;
  }>;
  isProcessing: boolean;
  showSummary: boolean;
}

function ChatInterfaceContent() {
  const { showToast } = useToast();

  // Models
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);

  // Conversations
  const [conversations, setConversations] = useState<Chat[]>([]);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [activeChatType, setActiveChatType] = useState<ChatType | null>(null);
  const [activeModelId, setActiveModelId] = useState<string | null>(null);

  // Sidebar state
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Messages for active chat
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  // Council state
  const [councilState, setCouncilState] = useState<CouncilState>({
    stage: 'idle',
    stageMessage: '',
    responses: [],
    reviews: [],
    isProcessing: false,
    showSummary: false,
  });

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load models on mount
  useEffect(() => {
    loadModels();
    loadConversationsFromStorage();
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+N: New chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        handleNewChat('council');
      }
      // Ctrl+B: Toggle sidebar
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        setIsSidebarOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, councilState.responses]);

  const loadModels = async () => {
    try {
      const fetchedModels = await fetchModels();
      setModels(fetchedModels);
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const loadConversationsFromStorage = () => {
    try {
      const stored = localStorage.getItem('llm_council_conversations');
      if (stored) {
        setConversations(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const saveConversationsToStorage = (convs: Chat[]) => {
    try {
      localStorage.setItem('llm_council_conversations', JSON.stringify(convs));
    } catch (error) {
      console.error('Failed to save conversations:', error);
    }
  };

  const loadMessagesFromStorage = (chatId: string) => {
    try {
      const stored = localStorage.getItem(`llm_council_messages_${chatId}`);
      if (stored) {
        setMessages(JSON.parse(stored));
      } else {
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    }
  };

  const saveMessagesToStorage = (chatId: string, msgs: Message[]) => {
    try {
      localStorage.setItem(`llm_council_messages_${chatId}`, JSON.stringify(msgs));
    } catch (error) {
      console.error('Failed to save messages:', error);
    }
  };

  const handleNewChat = (type: ChatType, modelId?: string) => {
    const chatId = `${type}_${Date.now()}`;
    const modelName = modelId
      ? models.find((m) => m.id === modelId)?.name || modelId
      : 'Council Group';

    const newChat: Chat = {
      id: chatId,
      type,
      name: type === 'council' ? 'Council Group' : modelName,
      modelId,
      timestamp: Date.now(),
    };

    const updatedConversations = [newChat, ...conversations];
    setConversations(updatedConversations);
    saveConversationsToStorage(updatedConversations);

    setActiveChat(chatId);
    setActiveChatType(type);
    setActiveModelId(modelId || null);
    setMessages([]);
    setCouncilState({
      stage: 'idle',
      stageMessage: '',
      responses: [],
      reviews: [],
      isProcessing: false,
      showSummary: false,
    });

    // Close sidebar on mobile after creating chat
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  const handleDeleteChat = (chatId: string) => {
    // Remove conversation
    const updatedConversations = conversations.filter((c) => c.id !== chatId);
    setConversations(updatedConversations);
    saveConversationsToStorage(updatedConversations);

    // Remove messages
    localStorage.removeItem(`llm_council_messages_${chatId}`);

    // If deleted chat was active, clear active state
    if (activeChat === chatId) {
      setActiveChat(null);
      setActiveChatType(null);
      setActiveModelId(null);
      setMessages([]);
      setCouncilState({
        stage: 'idle',
        stageMessage: '',
        responses: [],
        reviews: [],
        isProcessing: false,
        showSummary: false,
      });
    }
  };

  const handleClearAll = () => {
    // Clear all conversations
    setConversations([]);
    saveConversationsToStorage([]);

    // Clear all message data
    Object.keys(localStorage).forEach((key) => {
      if (key.startsWith('llm_council_messages_')) {
        localStorage.removeItem(key);
      }
    });

    // Reset active state
    setActiveChat(null);
    setActiveChatType(null);
    setActiveModelId(null);
    setMessages([]);
    setCouncilState({
      stage: 'idle',
      stageMessage: '',
      responses: [],
      reviews: [],
      isProcessing: false,
      showSummary: false,
    });
  };

  const handleSelectChat = (chatId: string) => {
    const chat = conversations.find((c) => c.id === chatId);
    if (!chat) return;

    setActiveChat(chatId);
    setActiveChatType(chat.type);
    setActiveModelId(chat.modelId || null);
    loadMessagesFromStorage(chatId);
    setCouncilState({
      stage: 'idle',
      stageMessage: '',
      responses: [],
      reviews: [],
      isProcessing: false,
      showSummary: false,
    });

    // Close sidebar on mobile after selecting chat
    if (window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  const updateConversationLastMessage = (chatId: string, message: string) => {
    const updatedConversations = conversations.map((conv) =>
      conv.id === chatId
        ? { ...conv, lastMessage: message.substring(0, 50), timestamp: Date.now() }
        : conv
    );
    setConversations(updatedConversations);
    saveConversationsToStorage(updatedConversations);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading || !activeChat || !activeChatType) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: input.trim(),
      sender: 'You',
      isUser: true,
      timestamp: Date.now(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    saveMessagesToStorage(activeChat, newMessages);
    updateConversationLastMessage(activeChat, input.trim());

    const userInput = input.trim();
    setInput('');
    setLoading(true);

    if (activeChatType === 'individual' && activeModelId) {
      // Individual model chat
      await handleIndividualChat(userInput, newMessages);
    } else if (activeChatType === 'council') {
      // Council group chat
      await handleCouncilChat(userInput, newMessages);
    }

    setLoading(false);
  };

  const handleIndividualChat = async (userInput: string, currentMessages: Message[]) => {
    if (!activeModelId) return;

    const modelName = models.find((m) => m.id === activeModelId)?.name || 'Model';

    // Build conversation history for context
    const conversationHistory = currentMessages
      .filter((msg) => msg.isUser || msg.modelId === activeModelId)
      .map((msg) => ({
        role: msg.isUser ? 'user' : 'assistant',
        content: msg.content,
      }));

    let fullResponse = '';

    try {
      await streamIndividualChat(
        activeModelId,
        userInput,
        conversationHistory,
        (chunk) => {
          if (chunk.type === 'content' && chunk.content) {
            fullResponse += chunk.content;
          } else if (chunk.type === 'complete') {
            // Save the complete message
            const assistantMessage: Message = {
              id: Date.now().toString(),
              content: fullResponse,
              sender: modelName,
              isUser: false,
              timestamp: Date.now(),
              modelId: activeModelId,
            };

            const updatedMessages = [...currentMessages, assistantMessage];
            setMessages(updatedMessages);
            saveMessagesToStorage(activeChat!, updatedMessages);
            updateConversationLastMessage(activeChat!, fullResponse);
          } else if (chunk.type === 'error') {
            console.error('Individual chat error:', chunk.content);
          }
        }
      );
    } catch (error) {
      console.error('Individual chat error:', error);
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: 'Sorry, an error occurred. Please try again.',
        sender: modelName,
        isUser: false,
        timestamp: Date.now(),
        modelId: activeModelId,
      };
      const updatedMessages = [...currentMessages, errorMessage];
      setMessages(updatedMessages);
      saveMessagesToStorage(activeChat!, updatedMessages);
    }
  };

  const handleCouncilChat = async (userInput: string, currentMessages: Message[]) => {
    setCouncilState({
      stage: 'first_opinions',
      stageMessage: 'Council members are thinking...',
      responses: [],
      reviews: [],
      isProcessing: true,
      showSummary: false,
    });

    let fullFinalResponse = '';
    const councilResponses: Array<{ modelId: string; content: string; timestamp: number }> = [];
    const councilReviews: Array<{
      reviewer_model: string;
      rankings: Array<{ model_id: string; rank: number; reasoning: string }>;
    }> = [];

    try {
      await streamChat(
        userInput,
        null, // conversation ID - we manage our own now
        null, // selected models
        (chunk: StreamChunk) => {
          switch (chunk.type) {
            case 'stage_update':
              if (chunk.stage) {
                setCouncilState((prev) => ({
                  ...prev,
                  stage: chunk.stage as Stage,
                  stageMessage: chunk.content || '',
                }));
              }
              break;

            case 'model_response':
              if (chunk.model_id && chunk.content) {
                const modelName =
                  models.find((m) => m.id === chunk.model_id)?.name ||
                  chunk.model_id.split('/').pop()?.split(':')[0] ||
                  chunk.model_id;

                const modelMessage: Message = {
                  id: `${Date.now()}_${chunk.model_id}`,
                  content: chunk.content,
                  sender: modelName,
                  isUser: false,
                  timestamp: Date.now(),
                  modelId: chunk.model_id,
                };

                councilResponses.push({
                  modelId: chunk.model_id,
                  content: chunk.content,
                  timestamp: Date.now(),
                });

                setMessages((prev) => {
                  const updated = [...prev, modelMessage];
                  saveMessagesToStorage(activeChat!, updated);
                  return updated;
                });
              }
              break;

            case 'review':
              if (chunk.model_id && chunk.data) {
                councilReviews.push({
                  reviewer_model: chunk.model_id,
                  rankings: chunk.data.rankings || [],
                });
              }
              break;

            case 'final_response':
              if (chunk.content) {
                fullFinalResponse += chunk.content;
              }
              break;

            case 'complete':
              if (fullFinalResponse) {
                const chairmanMessage: Message = {
                  id: `${Date.now()}_chairman`,
                  content: fullFinalResponse,
                  sender: 'Council Chairman (GPT-5.2)',
                  isUser: false,
                  timestamp: Date.now(),
                  modelId: 'gpt-5.2',
                };

                setMessages((prev) => {
                  const updated = [...prev, chairmanMessage];
                  saveMessagesToStorage(activeChat!, updated);
                  return updated;
                });

                updateConversationLastMessage(activeChat!, fullFinalResponse);
              }

              setCouncilState({
                stage: 'complete',
                stageMessage: '',
                responses: councilResponses,
                reviews: councilReviews,
                isProcessing: false,
                showSummary: councilReviews.length > 0,
              });
              break;

            case 'error':
              console.error('Stream error:', chunk.content);
              setCouncilState((prev) => ({ ...prev, isProcessing: false }));
              break;
          }
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      setCouncilState((prev) => ({ ...prev, isProcessing: false }));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getActiveChatName = () => {
    if (!activeChat) return '';
    const chat = conversations.find((c) => c.id === activeChat);
    return chat?.name || '';
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <AdvancedSidebar
        models={models}
        conversations={conversations}
        activeChat={activeChat}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onClearAll={handleClearAll}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            {/* Chat Header */}
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {/* Mobile Sidebar Toggle */}
                  <button
                    onClick={() => setIsSidebarOpen(true)}
                    className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    title="Toggle sidebar"
                  >
                    <svg className="w-6 h-6 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>

                  <span className="text-2xl">
                    {activeChatType === 'council' ? '🏛️' : '🤖'}
                  </span>
                  <div>
                    <h2 className="font-semibold text-gray-900 dark:text-white">{getActiveChatName()}</h2>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {activeChatType === 'council'
                        ? `${models.length} members`
                        : 'Individual chat'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-4 bg-gray-50 dark:bg-gray-900">
              {/* Stage Indicator for Council */}
              {activeChatType === 'council' && councilState.isProcessing && (
                <div className="mb-4">
                  <StageIndicator
                    currentStage={councilState.stage}
                    stageMessage={councilState.stageMessage}
                  />
                </div>
              )}

              {/* Messages */}
              <div className="max-w-4xl mx-auto">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-96">
                    <div className="text-center">
                      <span className="text-6xl mb-4 block">
                        {activeChatType === 'council' ? '🏛️' : '🤖'}
                      </span>
                      <p className="text-gray-500 dark:text-gray-400">
                        {activeChatType === 'council'
                          ? 'Ask a question to the council!'
                          : 'Start chatting with this model!'}
                      </p>
                    </div>
                  </div>
                ) : (
                  <>
                    {messages.map((message) => (
                      <MessageBubble
                        key={message.id}
                        content={message.content}
                        sender={message.sender}
                        isUser={message.isUser}
                        timestamp={message.timestamp}
                        modelId={message.modelId}
                      />
                    ))}

                    {/* Council Summary Card */}
                    {activeChatType === 'council' && councilState.showSummary && (
                      <CouncilSummaryCard
                        rankings={councilState.reviews}
                        models={models}
                      />
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
              <div className="max-w-4xl mx-auto flex gap-3">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type a message..."
                  className="flex-1 px-4 py-3 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                  rows={1}
                  disabled={loading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={loading || !input.trim()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {loading ? '...' : '➤'}
                </button>
              </div>
            </div>
          </>
        ) : (
          /* No Chat Selected */
          <div className="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900">
            <div className="text-center">
              <span className="text-8xl mb-6 block">🏛️</span>
              <h2 className="text-2xl font-bold text-gray-300 dark:text-gray-600 mb-2">Welcome to LLM Council</h2>
              <p className="text-gray-500 dark:text-gray-400 mb-6">
                Select a conversation or start a new chat
              </p>
              <div className="space-y-2 text-sm text-gray-400 dark:text-gray-500">
                <p>💬 Council Group: All models collaborate</p>
                <p>🤖 Individual: Chat with specific models</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function NewChatInterface() {
  return (
    <ToastProvider>
      <ChatInterfaceContent />
    </ToastProvider>
  );
}
