'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
  const [sources, setSources] = useState<DocumentSource[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [selectedSourceId, setSelectedSourceId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const [showNewSourceForm, setShowNewSourceForm] = useState(false);
  const [newSourceName, setNewSourceName] = useState('');
  const [newSourceDescription, setNewSourceDescription] = useState('');
  const [creatingSource, setCreatingSource] = useState(false);

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

  const filteredDocuments = selectedSourceId
    ? documents.filter((d) => d.source_id === selectedSourceId)
    : documents;

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

  const statCards = [
    {
      label: 'Sources',
      value: stats?.sources.active || 0,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
    },
    {
      label: 'Documents',
      value: stats?.documents.completed || 0,
      subtext: stats?.documents.processing ? `${stats.documents.processing} processing` : null,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      gradient: 'var(--gradient-accent)',
    },
    {
      label: 'Chunks',
      value: stats?.chunks.total || 0,
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
        </svg>
      ),
      gradient: 'var(--gradient-warm)',
    },
    {
      label: 'Conflicts',
      value: stats?.conflicts.unresolved || 0,
      subtext: 'unresolved',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      gradient: 'linear-gradient(135deg, #f43f5e 0%, #ec4899 100%)',
    },
  ];

  return (
    <div className="min-h-screen bg-mesh noise-bg">
      <div className="relative z-10 p-8">
        {/* Header */}
        <div className="mb-10 animate-slide-up">
          <div className="flex items-center gap-3 mb-2">
            <span
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'var(--color-accent-muted)',
                color: 'var(--color-accent)'
              }}
            >
              Knowledge Base
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
            Document Management
          </h1>
          <p className="mt-2 text-base" style={{ color: 'var(--color-text-secondary)' }}>
            Upload and manage documents for RAG-augmented council discussions.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10 animate-slide-up stagger-1">
          {statCards.map((card, index) => (
            <div
              key={card.label}
              className="rounded-2xl p-5 transition-all duration-300 hover:-translate-y-1"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)',
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="p-2 rounded-xl"
                  style={{ background: card.gradient }}
                >
                  <span style={{ color: 'var(--color-bg-primary)' }}>
                    {card.icon}
                  </span>
                </div>
              </div>
              <p className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
                {card.value.toLocaleString()}
              </p>
              <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                {card.label}
              </p>
              {card.subtext && (
                <p className="text-xs mt-1" style={{ color: 'var(--color-accent)' }}>
                  {card.subtext}
                </p>
              )}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column: Upload & Sources */}
          <div className="lg:col-span-1 space-y-6 animate-slide-up stagger-2">
            {/* Upload Section */}
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div className="p-6 border-b" style={{ borderColor: 'var(--color-border)' }}>
                <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                  Upload Documents
                </h2>
                <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                  Drag and drop or click to upload
                </p>
              </div>
              <div className="p-6">
                <DocumentUploader
                  sources={sources}
                  selectedSourceId={selectedSourceId}
                  onUploadComplete={loadData}
                  onSourceChange={setSelectedSourceId}
                />
              </div>
            </div>

            {/* Sources Section */}
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border)' }}>
                <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                  Sources
                </h2>
                <button
                  onClick={() => setShowNewSourceForm(!showNewSourceForm)}
                  className="text-sm font-medium transition-colors"
                  style={{ color: 'var(--color-accent)' }}
                >
                  {showNewSourceForm ? 'Cancel' : '+ Add'}
                </button>
              </div>

              <div className="p-4">
                {/* New source form */}
                {showNewSourceForm && (
                  <form
                    onSubmit={handleCreateSource}
                    className="mb-4 p-4 rounded-xl"
                    style={{ background: 'var(--color-bg-tertiary)' }}
                  >
                    <input
                      type="text"
                      value={newSourceName}
                      onChange={(e) => setNewSourceName(e.target.value)}
                      placeholder="Source name"
                      className="w-full px-4 py-3 rounded-xl text-sm mb-3"
                      style={{
                        background: 'var(--color-bg-secondary)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-primary)'
                      }}
                      required
                    />
                    <input
                      type="text"
                      value={newSourceDescription}
                      onChange={(e) => setNewSourceDescription(e.target.value)}
                      placeholder="Description (optional)"
                      className="w-full px-4 py-3 rounded-xl text-sm mb-3"
                      style={{
                        background: 'var(--color-bg-secondary)',
                        border: '1px solid var(--color-border)',
                        color: 'var(--color-text-primary)'
                      }}
                    />
                    <button
                      type="submit"
                      disabled={creatingSource}
                      className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50"
                      style={{
                        background: 'var(--gradient-accent)',
                        color: 'var(--color-bg-primary)'
                      }}
                    >
                      {creatingSource ? 'Creating...' : 'Create Source'}
                    </button>
                  </form>
                )}

                {/* Sources list */}
                <div className="space-y-2">
                  {sources.length === 0 ? (
                    <p className="text-sm text-center py-4" style={{ color: 'var(--color-text-muted)' }}>
                      No sources yet. Create one to get started.
                    </p>
                  ) : (
                    sources.map((source) => (
                      <div
                        key={source.id}
                        onClick={() => setSelectedSourceId(source.id)}
                        className="p-4 rounded-xl cursor-pointer transition-all duration-200"
                        style={{
                          background: selectedSourceId === source.id
                            ? 'var(--color-accent-muted)'
                            : 'var(--color-bg-tertiary)',
                          border: `1px solid ${selectedSourceId === source.id ? 'var(--color-accent)' : 'transparent'}`
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p
                              className="font-medium text-sm"
                              style={{
                                color: selectedSourceId === source.id
                                  ? 'var(--color-accent)'
                                  : 'var(--color-text-primary)'
                              }}
                            >
                              {source.name}
                            </p>
                            <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                              {source.document_count} documents
                            </p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSource(source);
                            }}
                            className="p-1.5 rounded-lg transition-colors"
                            style={{
                              color: 'var(--color-error)',
                              background: 'var(--color-error-muted)'
                            }}
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Right column: Document list */}
          <div className="lg:col-span-2 animate-slide-up stagger-3">
            <div
              className="rounded-2xl overflow-hidden h-full"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div className="p-6 border-b flex items-center justify-between" style={{ borderColor: 'var(--color-border)' }}>
                <div>
                  <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                    Documents
                  </h2>
                  <p className="text-sm mt-1" style={{ color: 'var(--color-text-muted)' }}>
                    {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''}
                    {selectedSourceId && sources.find(s => s.id === selectedSourceId) && (
                      <span> in {sources.find(s => s.id === selectedSourceId)?.name}</span>
                    )}
                  </p>
                </div>
                <button
                  onClick={loadData}
                  className="p-2 rounded-xl transition-all duration-200"
                  style={{
                    background: 'var(--color-bg-tertiary)',
                    color: 'var(--color-text-muted)'
                  }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
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
    </div>
  );
}
