/**
 * API client for communicating with the LLM Council backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
  type: 'stage_update' | 'model_response' | 'review' | 'final_response' | 'error' | 'complete';
  stage?: string;
  model_id?: string;
  content?: string;
  data?: any;
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
  const response = await fetch(`${API_BASE_URL}/models/`);
  if (!response.ok) {
    throw new Error('Failed to fetch models');
  }
  return response.json();
}

/**
 * Fetch chairman model info.
 */
export async function fetchChairman(): Promise<{ chairman_model: string; provider: string }> {
  const response = await fetch(`${API_BASE_URL}/models/chairman`);
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
 */
export async function streamChat(
  message: string,
  conversationId: string | null,
  selectedModels: string[] | null,
  onChunk: (chunk: StreamChunk) => void
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      selected_models: selectedModels,
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
  const response = await fetch(`${API_BASE_URL}/chat/history/${conversationId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch conversation history');
  }
  return response.json();
}

/**
 * List all conversations.
 */
export async function fetchConversations(): Promise<ConversationHistory[]> {
  const response = await fetch(`${API_BASE_URL}/chat/conversations`);
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
    headers: {
      'Content-Type': 'application/json',
    },
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
