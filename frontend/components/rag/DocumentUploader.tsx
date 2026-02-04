'use client';

import React, { useState, useCallback, useRef } from 'react';
import { uploadDocument, DocumentSource } from '@/lib/rag-api';

interface DocumentUploaderProps {
  sources: DocumentSource[];
  selectedSourceId: number | null;
  onUploadComplete: () => void;
  onSourceChange: (sourceId: number) => void;
}

export default function DocumentUploader({
  sources,
  selectedSourceId,
  onUploadComplete,
  onSourceChange,
}: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedTypes = ['pdf', 'docx', 'doc', 'txt', 'md', 'markdown'];

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const validateFile = (file: File): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !allowedTypes.includes(extension)) {
      setError(`Unsupported file type. Allowed: ${allowedTypes.join(', ')}`);
      return false;
    }
    if (file.size > 50 * 1024 * 1024) {
      setError('File too large. Maximum size: 50MB');
      return false;
    }
    return true;
  };

  const uploadFile = async (file: File) => {
    if (!selectedSourceId) {
      setError('Please select a source first');
      return;
    }

    if (!validateFile(file)) {
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(`Uploading ${file.name}...`);

    try {
      const result = await uploadDocument(file, selectedSourceId);
      setUploadProgress(`${result.message}`);
      setTimeout(() => {
        setUploadProgress(null);
        onUploadComplete();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    for (const file of files) {
      await uploadFile(file);
    }
  }, [selectedSourceId]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    for (const file of files) {
      await uploadFile(file);
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4">
      {/* Source selector */}
      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          Upload to Source
        </label>
        <select
          value={selectedSourceId || ''}
          onChange={(e) => onSourceChange(Number(e.target.value))}
          className="w-full px-4 py-3 rounded-xl text-sm appearance-none cursor-pointer"
          style={{
            background: 'var(--color-bg-tertiary)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-primary)',
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%23606070'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 12px center',
            backgroundSize: '20px',
          }}
        >
          <option value="">Select a source...</option>
          {sources.filter(s => s.is_active).map((source) => (
            <option key={source.id} value={source.id}>
              {source.name} ({source.document_count} docs)
            </option>
          ))}
        </select>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className="relative rounded-xl p-8 text-center cursor-pointer transition-all duration-200"
        style={{
          background: isDragging ? 'var(--color-accent-muted)' : 'var(--color-bg-tertiary)',
          border: `2px dashed ${isDragging ? 'var(--color-accent)' : 'var(--color-border)'}`,
          opacity: !selectedSourceId ? 0.5 : 1,
          cursor: !selectedSourceId ? 'not-allowed' : 'pointer',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={allowedTypes.map(t => `.${t}`).join(',')}
          onChange={handleFileSelect}
          className="hidden"
          disabled={!selectedSourceId || uploading}
        />

        {uploading ? (
          <div className="flex flex-col items-center space-y-3">
            <div
              className="w-10 h-10 rounded-full animate-spin"
              style={{
                border: '3px solid var(--color-bg-secondary)',
                borderTopColor: 'var(--color-accent)'
              }}
            />
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {uploadProgress}
            </p>
          </div>
        ) : (
          <>
            <div
              className="w-14 h-14 mx-auto mb-4 rounded-2xl flex items-center justify-center"
              style={{ background: 'var(--color-accent-muted)' }}
            >
              <svg
                className="w-7 h-7"
                style={{ color: 'var(--color-accent)' }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <p className="text-sm mb-1" style={{ color: 'var(--color-text-primary)' }}>
              <span style={{ color: 'var(--color-accent)' }}>Click to upload</span> or drag and drop
            </p>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              PDF, DOCX, TXT, MD up to 50MB
            </p>
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div
          className="p-4 rounded-xl flex items-start gap-3"
          style={{
            background: 'var(--color-error-muted)',
            border: '1px solid rgba(255, 68, 102, 0.2)'
          }}
        >
          <svg
            className="w-5 h-5 flex-shrink-0"
            style={{ color: 'var(--color-error)' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm" style={{ color: 'var(--color-error)' }}>{error}</p>
        </div>
      )}

      {/* Success message */}
      {uploadProgress && !uploading && (
        <div
          className="p-4 rounded-xl flex items-start gap-3"
          style={{
            background: 'var(--color-success-muted)',
            border: '1px solid rgba(0, 255, 136, 0.2)'
          }}
        >
          <svg
            className="w-5 h-5 flex-shrink-0"
            style={{ color: 'var(--color-success)' }}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <p className="text-sm" style={{ color: 'var(--color-success)' }}>{uploadProgress}</p>
        </div>
      )}
    </div>
  );
}
