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
    // 50MB limit
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

    // Upload files one by one
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

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4">
      {/* Source selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Upload to Source
        </label>
        <select
          value={selectedSourceId || ''}
          onChange={(e) => onSourceChange(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
          ${isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${!selectedSourceId ? 'opacity-50 cursor-not-allowed' : ''}
        `}
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
          <div className="flex flex-col items-center space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p className="text-sm text-gray-600">{uploadProgress}</p>
          </div>
        ) : (
          <>
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500 mt-1">
              PDF, DOCX, TXT, MD up to 50MB
            </p>
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Success message */}
      {uploadProgress && !uploading && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-600">{uploadProgress}</p>
        </div>
      )}
    </div>
  );
}
