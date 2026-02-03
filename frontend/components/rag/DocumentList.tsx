'use client';

import React, { useState } from 'react';
import { Document, DocumentStatus, deleteDocument, reindexDocument } from '@/lib/rag-api';

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  onRefresh: () => void;
}

const statusColors: Record<DocumentStatus, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  processing: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
};

const statusIcons: Record<DocumentStatus, string> = {
  pending: '...',
  processing: '...',
  completed: 'OK',
  failed: '!!',
};

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatFileType(fileType: string | null): string {
  if (!fileType) return 'unknown';
  return fileType.toUpperCase();
}

export default function DocumentList({ documents, loading, onRefresh }: DocumentListProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [reindexingId, setReindexingId] = useState<number | null>(null);

  const handleDelete = async (doc: Document) => {
    if (!confirm(`Delete "${doc.title}"? This cannot be undone.`)) return;

    setDeletingId(doc.id);
    try {
      await deleteDocument(doc.id);
      onRefresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete document');
    } finally {
      setDeletingId(null);
    }
  };

  const handleReindex = async (doc: Document) => {
    setReindexingId(doc.id);
    try {
      await reindexDocument(doc.id);
      alert('Reindex task queued');
      onRefresh();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to reindex document');
    } finally {
      setReindexingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No documents found</p>
        <p className="text-sm mt-1">Upload documents to get started</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Document
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Source
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Chunks
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Created
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {documents.map((doc) => (
            <tr key={doc.id} className="hover:bg-gray-50">
              <td className="px-4 py-3">
                <div className="flex flex-col">
                  <span className="text-sm font-medium text-gray-900 truncate max-w-xs" title={doc.title}>
                    {doc.title}
                  </span>
                  {doc.author && (
                    <span className="text-xs text-gray-500">by {doc.author}</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {doc.source_name}
              </td>
              <td className="px-4 py-3">
                <span className="px-2 py-1 text-xs font-medium bg-gray-100 rounded">
                  {formatFileType(doc.file_type)}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 text-xs font-medium rounded ${statusColors[doc.status]}`}>
                  {statusIcons[doc.status]} {doc.status}
                </span>
                {doc.error_message && (
                  <p className="text-xs text-red-500 mt-1 truncate max-w-xs" title={doc.error_message}>
                    {doc.error_message}
                  </p>
                )}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {doc.chunk_count > 0 ? (
                  <span title={`${doc.token_count} tokens`}>
                    {doc.chunk_count} chunks
                  </span>
                ) : (
                  '-'
                )}
              </td>
              <td className="px-4 py-3 text-sm text-gray-500">
                {formatDate(doc.created_at)}
              </td>
              <td className="px-4 py-3 text-right space-x-2">
                {doc.status === 'completed' && (
                  <button
                    onClick={() => handleReindex(doc)}
                    disabled={reindexingId === doc.id}
                    className="text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50"
                  >
                    {reindexingId === doc.id ? '...' : 'Reindex'}
                  </button>
                )}
                <button
                  onClick={() => handleDelete(doc)}
                  disabled={deletingId === doc.id}
                  className="text-xs text-red-600 hover:text-red-800 disabled:opacity-50"
                >
                  {deletingId === doc.id ? '...' : 'Delete'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
