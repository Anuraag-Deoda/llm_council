'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import DocumentUploader from '@/components/rag/DocumentUploader';
import DocumentList from '@/components/rag/DocumentList';
import {
  fetchSources,
  fetchDocuments,
  fetchRAGStats,
  createSource,
  deleteSource,
  DocumentSource,
  Document,
  RAGStats,
} from '@/lib/rag-api';

export default function KnowledgeBasePage() {
  // State
  const [sources, setSources] = useState<DocumentSource[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // New source form
  const [showNewSourceForm, setShowNewSourceForm] = useState(false);
  const [newSourceName, setNewSourceName] = useState('');
  const [newSourceDescription, setNewSourceDescription] = useState('');
  const [creatingSource, setCreatingSource] = useState(false);

  // Load data
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [sourcesData, docsData, statsData] = await Promise.all([
        fetchSources(),
        fetchDocuments({ page_size: 50 }),
        fetchRAGStats(),
      ]);
      setSources(sourcesData);
      setDocuments(docsData.documents);
      setStats(statsData);

      // Auto-select first source if none selected
      if (!selectedSourceId && sourcesData.length > 0) {
        setSelectedSourceId(sourcesData[0].id);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSourceId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filter documents by selected source
  const filteredDocuments = selectedSourceId
    ? documents.filter((d) => d.source_id === selectedSourceId)
    : documents;

  // Create new source
  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSourceName.trim()) return;

    setCreatingSource(true);
    try {
      await createSource({
        name: newSourceName,
        description: newSourceDescription || undefined,
      });
      setNewSourceName('');
      setNewSourceDescription('');
      setShowNewSourceForm(false);
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create source');
    } finally {
      setCreatingSource(false);
    }
  };

  // Delete source
  const handleDeleteSource = async (source: DocumentSource) => {
    if (!confirm(`Delete source "${source.name}" and all its documents?`)) return;

    try {
      await deleteSource(source.id);
      if (selectedSourceId === source.id) {
        setSelectedSourceId(null);
      }
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete source');
    }
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="text-gray-600 mt-1">
          Manage documents for RAG-augmented council discussions
        </p>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Sources</p>
            <p className="text-2xl font-bold text-gray-900">{stats.sources.active}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Documents</p>
            <p className="text-2xl font-bold text-gray-900">{stats.documents.completed}</p>
            {stats.documents.processing > 0 && (
              <p className="text-xs text-indigo-600">{stats.documents.processing} processing</p>
            )}
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Chunks</p>
            <p className="text-2xl font-bold text-gray-900">{stats.chunks.total}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">Conflicts</p>
            <p className="text-2xl font-bold text-gray-900">{stats.conflicts.unresolved}</p>
            <p className="text-xs text-gray-500">unresolved</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column: Upload */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
            <DocumentUploader
              sources={sources}
              selectedSourceId={selectedSourceId}
              onUploadComplete={loadData}
              onSourceChange={setSelectedSourceId}
            />
          </div>

          {/* Sources section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Sources</h2>
              <button
                onClick={() => setShowNewSourceForm(!showNewSourceForm)}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                {showNewSourceForm ? 'Cancel' : '+ Add Source'}
              </button>
            </div>

            {/* New source form */}
            {showNewSourceForm && (
              <form onSubmit={handleCreateSource} className="mb-4 p-4 bg-gray-50 rounded-lg">
                <input
                  type="text"
                  value={newSourceName}
                  onChange={(e) => setNewSourceName(e.target.value)}
                  placeholder="Source name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 text-sm"
                  required
                />
                <input
                  type="text"
                  value={newSourceDescription}
                  onChange={(e) => setNewSourceDescription(e.target.value)}
                  placeholder="Description (optional)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 text-sm"
                />
                <button
                  type="submit"
                  disabled={creatingSource}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {creatingSource ? 'Creating...' : 'Create Source'}
                </button>
              </form>
            )}

            {/* Sources list */}
            <div className="space-y-2">
              {sources.length === 0 ? (
                <p className="text-sm text-gray-500">No sources. Create one to get started.</p>
              ) : (
                sources.map((source) => (
                  <div
                    key={source.id}
                    className={`p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedSourceId === source.id
                        ? 'bg-indigo-50 border border-indigo-200'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                    onClick={() => setSelectedSourceId(source.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{source.name}</p>
                        <p className="text-xs text-gray-500">
                          {source.document_count} documents
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSource(source);
                        }}
                        className="text-xs text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right column: Document list */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="border-b border-gray-200 px-6 py-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">
                  Documents
                  {selectedSourceId && (
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      ({filteredDocuments.length})
                    </span>
                  )}
                </h2>
                <button
                  onClick={loadData}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  Refresh
                </button>
              </div>
            </div>
            <div className="p-6">
              <DocumentList
                documents={filteredDocuments}
                loading={loading}
                onRefresh={loadData}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
