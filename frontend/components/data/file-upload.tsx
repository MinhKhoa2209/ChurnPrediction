/**
 * File Upload Component
 * Reusable drag-and-drop file upload component for CSV files

'use client';

import { useState, useCallback, DragEvent, ChangeEvent, useRef } from 'react';
import { announceToScreenReader } from '@/lib/accessibility';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  maxSizeMB?: number;
  accept?: string;
  disabled?: boolean;
}

export function FileUpload({
  onFileSelect,
  maxSizeMB = 50,
  accept = '.csv',
  disabled = false,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): boolean => {
      setError(null);

      // Check file type
      if (!file.name.endsWith('.csv')) {
        const errorMsg = 'Only CSV files are accepted';
        setError(errorMsg);
        announceToScreenReader(errorMsg, 'assertive');
        return false;
      }

      // Check file size (Requirement 3.1: max 50MB)
      const maxSizeBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        const errorMsg = `File too large. Maximum size is ${maxSizeMB}MB. Your file is ${(file.size / (1024 * 1024)).toFixed(2)}MB.`;
        setError(errorMsg);
        announceToScreenReader(errorMsg, 'assertive');
        return false;
      }

      return true;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    (file: File) => {
      if (validateFile(file)) {
        announceToScreenReader(`File ${file.name} selected successfully`, 'polite');
        onFileSelect(file);
      }
    },
    [validateFile, onFileSelect]
  );

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled) return;

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [disabled, handleFile]
  );

  const handleFileInput = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      // Requirement 28.2: Keyboard navigation support
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInputRef.current?.click();
      }
    },
    []
  );

  return (
    <div className="w-full">
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="File upload area. Click or press Enter to select a CSV file, or drag and drop a file here"
        aria-disabled={disabled}
        onKeyDown={handleKeyDown}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400 dark:hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInput}
          disabled={disabled}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          aria-label="File upload input"
          tabIndex={-1}
        />
        
        <div className="space-y-4">
          <div className="flex justify-center">
            <svg
              className="w-16 h-16 text-gray-400 dark:text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
              role="img"
            >
              <title>Upload icon</title>
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          
          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              {isDragging ? 'Drop your file here' : 'Drag and drop your CSV file here'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              or click to browse
            </p>
          </div>
          
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p>Accepts: CSV files only</p>
            <p>Maximum size: {maxSizeMB}MB</p>
          </div>
        </div>
      </div>

      {error && (
        <div 
          className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
          role="alert"
          aria-live="assertive"
        >
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}
    </div>
  );
}
