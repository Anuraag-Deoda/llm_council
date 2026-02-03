/**
 * RAG API client for the LLM Council knowledge base.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('llm_council_access_token');
}

// Helper to create headers with optional auth
function createHeaders(contentType: string | null = 'application/json'): HeadersInit {
  const headers: HeadersInit = {};

  if (contentType) {
    headers['Content-Type'] = contentType;
  }

  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

// ============================================================================
// Types
// ============================================================================

export type SourceType = 'document' | 'slack' | 'notion' | 'github' | 'web';
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type ConflictType = 'factual' | 'temporal' | 'opinion' | 'numerical' | 'procedural';
export type ConflictStatus = 'detected' | 'reviewed' | 'resolved' | 'dismissed';

export interface DocumentSource {
  id: number;
  name: string;
  source_type: SourceType;
  description: string | null;
  base_trust_score: number;
  is_active: boolean;
  document_count: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
  created_at: string;
}

export interface Document {
  id: number;
  source_id: number;
  source_name: string;
  title: string;
  file_type: string | null;
  status: DocumentStatus;
  chunk_count: number;
  token_count: number;
  author: string | null;
  error_message: string | null;
  created_at: string;
  indexed_at: string | null;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  page_size: number;
}

export interface ChunkScore {
  final: number;
  similarity: number;
  source_trust: number;
  recency: number;
  author_authority: number;
}

export interface RetrievedChunk {
  chunk_id: number;
  document_id: number;
  document_title: string;
  source_name: string;
  source_type: string;
  content: string;
  section_title: string | null;
  scores: ChunkScore;
}

export interface DetectedConflict {
  type: ConflictType;
  confidence: number;
  source_a: string;
  source_b: string;
  explanation: string;
  recommendation: string;
}

export interface RAGQueryResponse {
  query: string;
  context: string;
  chunks: RetrievedChunk[];
  conflicts: DetectedConflict[];
  conflict_report: string;
  timing: {
    retrieval_ms: number;
    conflict_detection_ms: number;
    total_ms: number;
  };
}

export interface ConflictRecord {
  id: number;
  chunk_a_id: number;
  chunk_b_id: number;
  conflict_type: ConflictType;
  confidence: number;
  explanation: string | null;
  recommendation: string | null;
  status: ConflictStatus;
  resolved_by: string | null;
  resolution_notes: string | null;
  detected_at: string;
  resolved_at: string | null;
}

export interface RAGStats {
  sources: {
    total: number;
    active: number;
  };
  documents: {
    total: number;
    completed: number;
    failed: number;
    processing: number;
  };
  chunks: {
    total: number;
  };
  conflicts: {
    total: number;
    unresolved: number;
  };
  rag_enabled: boolean;
}

// ============================================================================
// Document Sources API
// ============================================================================

export async function createSource(data: {
  name: string;
  source_type?: SourceType;
  description?: string;
  base_trust_score?: number;
}): Promise<DocumentSource> {
  const response = await fetch(`${API_BASE_URL}/rag/sources`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create source');
  }
  return response.json();
}

export async function fetchSources(activeOnly: boolean = false): Promise<DocumentSource[]> {
  const params = new URLSearchParams();
  if (activeOnly) params.append('active_only', 'true');

  const response = await fetch(`${API_BASE_URL}/rag/sources?${params}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch sources');
  }
  return response.json();
}

export async function deleteSource(sourceId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/rag/sources/${sourceId}`, {
    method: 'DELETE',
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to delete source');
  }
}

export async function syncSource(sourceId: number, fullSync: boolean = false): Promise<{ task_id: string }> {
  const params = new URLSearchParams();
  if (fullSync) params.append('full_sync', 'true');

  const response = await fetch(`${API_BASE_URL}/rag/sources/${sourceId}/sync?${params}`, {
    method: 'POST',
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to sync source');
  }
  return response.json();
}

// ============================================================================
// Documents API
// ============================================================================

export async function uploadDocument(
  file: File,
  sourceId: number,
  title?: string,
  author?: string
): Promise<{
  document_id: number;
  title: string;
  status: DocumentStatus;
  file_type: string | null;
  task_id: string | null;
  message: string;
}> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_id', sourceId.toString());
  if (title) formData.append('title', title);
  if (author) formData.append('author', author);

  const response = await fetch(`${API_BASE_URL}/rag/documents/upload`, {
    method: 'POST',
    headers: createHeaders(null), // No content-type for multipart
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload document');
  }
  return response.json();
}

export async function fetchDocuments(params?: {
  source_id?: number;
  status?: DocumentStatus;
  page?: number;
  page_size?: number;
}): Promise<DocumentListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.source_id) searchParams.append('source_id', params.source_id.toString());
  if (params?.status) searchParams.append('status', params.status);
  if (params?.page) searchParams.append('page', params.page.toString());
  if (params?.page_size) searchParams.append('page_size', params.page_size.toString());

  const response = await fetch(`${API_BASE_URL}/rag/documents?${searchParams}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
}

export async function fetchDocument(documentId: number): Promise<Document> {
  const response = await fetch(`${API_BASE_URL}/rag/documents/${documentId}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch document');
  }
  return response.json();
}

export async function deleteDocument(documentId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/rag/documents/${documentId}`, {
    method: 'DELETE',
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to delete document');
  }
}

export async function reindexDocument(documentId: number): Promise<{ task_id: string }> {
  const response = await fetch(`${API_BASE_URL}/rag/documents/${documentId}/reindex`, {
    method: 'POST',
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to reindex document');
  }
  return response.json();
}

// ============================================================================
// RAG Query API
// ============================================================================

export async function queryRAG(params: {
  query: string;
  top_k?: number;
  source_ids?: number[];
  include_conflict_detection?: boolean;
}): Promise<RAGQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/rag/query`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to query RAG');
  }
  return response.json();
}

// ============================================================================
// Conflicts API
// ============================================================================

export async function fetchConflicts(params?: {
  status?: ConflictStatus;
  conflict_type?: ConflictType;
  limit?: number;
}): Promise<ConflictRecord[]> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.conflict_type) searchParams.append('conflict_type', params.conflict_type);
  if (params?.limit) searchParams.append('limit', params.limit.toString());

  const response = await fetch(`${API_BASE_URL}/rag/conflicts?${searchParams}`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch conflicts');
  }
  return response.json();
}

export async function resolveConflict(
  conflictId: number,
  data: {
    status: ConflictStatus;
    resolution_notes?: string;
    preferred_chunk_id?: number;
    resolved_by?: string;
  }
): Promise<ConflictRecord> {
  const response = await fetch(`${API_BASE_URL}/rag/conflicts/${conflictId}/resolve`, {
    method: 'POST',
    headers: createHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to resolve conflict');
  }
  return response.json();
}

// ============================================================================
// Stats API
// ============================================================================

export async function fetchRAGStats(): Promise<RAGStats> {
  const response = await fetch(`${API_BASE_URL}/rag/stats`, {
    headers: createHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch RAG stats');
  }
  return response.json();
}
