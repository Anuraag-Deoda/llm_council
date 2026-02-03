/**
 * API client for communicating with the LLM Council backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('llm_council_access_token');
}

// Helper to create headers with optional auth
function createHeaders(includeAuth: boolean = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (includeAuth) {
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  is_chairman: boolean;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface ModelResponse {
  model_id: string;
  response: string;
  timestamp: number;
  error?: string;
}

export interface ReviewResponse {
  reviewer_model: string;
  rankings: Array<{
    model_id: string;
    rank: number;
    reasoning: string;
  }>;
  timestamp: number;
}

export interface StreamChunk {
  type: 'stage_update' | 'model_response' | 'review' | 'final_response' | 'error' | 'complete' | 'rag_context' | 'conflict_detected';
  stage?: string;
  model_id?: string;
  content?: string;
  data?: any;
  timestamp?: string;
}

export interface ConversationHistory {
  conversation_id: string;
  messages: ChatMessage[];
  council_responses: any[];
  created_at: number;
  updated_at: number;
}

/**
 * Fetch available models from the backend.
 */
export async function fetchModels(): Promise<ModelInfo[]> {
  const response = await fetch(`${API_BASE_URL}/models/`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch models');
  }
  return response.json();
}

/**
 * Fetch chairman model info.
 */
export async function fetchChairman(): Promise<{ chairman_model: string; provider: string }> {
  const response = await fetch(`${API_BASE_URL}/models/chairman`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch chairman');
  }
  return response.json();
}

/**
 * Stream a chat response from the council.
 *
 * @param message - The user's message
 * @param conversationId - Optional conversation ID
 * @param selectedModels - Optional list of model IDs to use
 * @param onChunk - Callback for each streamed chunk
 * @param useRAG - Enable RAG augmentation
 * @param ragSourceIds - Filter RAG to specific source IDs
 */
export async function streamChat(
  message: string,
  conversationId: string | null,
  selectedModels: string[] | null,
  onChunk: (chunk: StreamChunk) => void,
  useRAG: boolean = false,
  ragSourceIds: number[] | null = null
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      selected_models: selectedModels,
      use_rag: useRAG,
      rag_source_ids: ragSourceIds,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to stream chat response');
  }

  const conversationIdFromHeader = response.headers.get('X-Conversation-ID');

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No reader available');
  }

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Split by newlines to process complete JSON chunks
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.trim()) {
        try {
          const chunk = JSON.parse(line) as StreamChunk;
          onChunk(chunk);
        } catch (e) {
          console.error('Failed to parse chunk:', line, e);
        }
      }
    }
  }

  return conversationIdFromHeader || '';
}

/**
 * Get conversation history.
 */
export async function fetchConversationHistory(conversationId: string): Promise<ConversationHistory> {
  const response = await fetch(`${API_BASE_URL}/chat/history/${conversationId}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch conversation history');
  }
  return response.json();
}

/**
 * List all conversations.
 */
export async function fetchConversations(): Promise<ConversationHistory[]> {
  const response = await fetch(`${API_BASE_URL}/chat/conversations`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch conversations');
  }
  return response.json();
}

/**
 * Delete a conversation.
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/history/${conversationId}`, {
    method: 'DELETE',
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to delete conversation');
  }
}

/**
 * Stream a chat response from a single model.
 *
 * @param modelId - The model to chat with
 * @param message - The user's message
 * @param conversationHistory - Optional conversation history
 * @param onChunk - Callback for each streamed chunk
 */
export async function streamIndividualChat(
  modelId: string,
  message: string,
  conversationHistory: Array<{ role: string; content: string }> | null,
  onChunk: (chunk: { type: string; content?: string }) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/individual/stream`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify({
      model_id: modelId,
      message,
      conversation_history: conversationHistory,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to stream individual chat response');
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No reader available');
  }

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Split by newlines to process complete JSON chunks
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.trim()) {
        try {
          const chunk = JSON.parse(line);
          onChunk(chunk);
        } catch (e) {
          console.error('Failed to parse chunk:', line, e);
        }
      }
    }
  }
}


// ============================================================================
// Analytics API
// ============================================================================

export interface LeaderboardEntry {
  rank: number;
  model_id: string;
  model_name: string;
  metric_value: number;
  metric_name: string;
}

export interface TrendData {
  timestamp: string;
  value: number;
  label: string;
}

export interface AnalyticsSummary {
  global_stats: {
    total_conversations: number;
    total_messages: number;
    total_tokens: number;
    total_cost: number;
    active_models: number;
  };
  conversation_breakdown: {
    council: number;
    individual: number;
  };
  recent_activity: {
    conversations_24h: number;
    messages_24h: number;
  };
}

/**
 * Fetch analytics summary
 */
export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const response = await fetch(`${API_BASE_URL}/analytics/summary`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch analytics summary');
  }
  return response.json();
}

/**
 * Fetch latency leaderboard
 */
export async function fetchLatencyLeaderboard(limit: number = 10): Promise<{ leaderboard: LeaderboardEntry[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/leaderboard/latency?limit=${limit}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch latency leaderboard');
  }
  return response.json();
}

/**
 * Fetch success rate leaderboard
 */
export async function fetchSuccessRateLeaderboard(limit: number = 10): Promise<{ leaderboard: LeaderboardEntry[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/leaderboard/success-rate?limit=${limit}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch success rate leaderboard');
  }
  return response.json();
}

/**
 * Fetch peer review leaderboard
 */
export async function fetchPeerReviewLeaderboard(limit: number = 10, days: number = 30): Promise<{ leaderboard: LeaderboardEntry[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/leaderboard/peer-review?limit=${limit}&days=${days}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch peer review leaderboard');
  }
  return response.json();
}

/**
 * Fetch usage trends
 */
export async function fetchUsageTrends(days: number = 7): Promise<{ trends: TrendData[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/trends/usage?days=${days}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch usage trends');
  }
  return response.json();
}

/**
 * Fetch cost trends
 */
export async function fetchCostTrends(days: number = 7): Promise<{ trends: TrendData[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/trends/cost?days=${days}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch cost trends');
  }
  return response.json();
}

/**
 * Fetch token trends
 */
export async function fetchTokenTrends(days: number = 7): Promise<{ trends: TrendData[] }> {
  const response = await fetch(`${API_BASE_URL}/analytics/trends/tokens?days=${days}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch token trends');
  }
  return response.json();
}


// ============================================================================
// RAG Stats API
// ============================================================================

export interface RAGStats {
  total_sources: number;
  total_documents: number;
  total_chunks: number;
  total_retrievals: number;
  pending_documents: number;
  failed_documents: number;
}

/**
 * Fetch RAG statistics
 */
export async function fetchRAGStats(): Promise<RAGStats> {
  const response = await fetch(`${API_BASE_URL}/rag/stats`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch RAG stats');
  }
  return response.json();
}
