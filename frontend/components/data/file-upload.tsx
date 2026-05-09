'use client';

import { useState, useCallback, DragEvent, ChangeEvent, useRef } from 'react';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { announceToScreenReader } from '@/lib/accessibility';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  maxSizeMB?: number;
  accept?: string;
  disabled?: boolean;
}

export function FileUpload({ onFileSelect, maxSizeMB = 50, accept = '.csv', disabled = false }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((file: File): boolean => {
    setError(null);

    if (!file.name.endsWith('.csv')) {
      const errorMsg = 'Only CSV files are accepted';
      setError(errorMsg);
      announceToScreenReader(errorMsg, 'assertive');
      return false;
    }

    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      const errorMsg = `File too large. Maximum size is ${maxSizeMB}MB. Your file is ${(file.size / (1024 * 1024)).toFixed(2)}MB.`;
      setError(errorMsg);
      announceToScreenReader(errorMsg, 'assertive');
      return false;
    }

    return true;
  }, [maxSizeMB]);

  const handleFile = useCallback((file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
      announceToScreenReader(`File ${file.name} selected successfully`, 'polite');
      onFileSelect(file);
    }
  }, [validateFile, onFileSelect]);

  const handleDragEnter = useCallback((e: DragEvent<HTMLDivElement>) => { e.preventDefault(); e.stopPropagation(); setIsDragging(true); }, []);
  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }, []);
  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => { e.preventDefault(); e.stopPropagation(); }, []);

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) handleFile(files[0]);
  }, [disabled, handleFile]);

  const handleFileInput = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) handleFile(files[0]);
  }, [handleFile]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInputRef.current?.click(); }
  }, []);

  const clearFile = () => {
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="w-full space-y-3">
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
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={cn(
          'relative border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer',
          isDragging
            ? 'border-primary bg-primary/5 scale-[1.01]'
            : 'border-border hover:border-primary/50 hover:bg-muted/30',
          disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
          selectedFile && 'border-emerald-400 dark:border-emerald-600 bg-emerald-50 dark:bg-emerald-900/10'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleFileInput}
          disabled={disabled}
          className="sr-only"
          aria-label="File upload input"
          tabIndex={-1}
        />

        <div className="space-y-4">
          <div className="flex justify-center">
            {selectedFile ? (
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900/30">
                <FileText className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
              </div>
            ) : (
              <div className={cn(
                'flex h-16 w-16 items-center justify-center rounded-2xl transition-colors',
                isDragging ? 'bg-primary/15' : 'bg-muted'
              )}>
                <Upload className={cn('h-8 w-8', isDragging ? 'text-primary' : 'text-muted-foreground')} />
              </div>
            )}
          </div>

          <div>
            {selectedFile ? (
              <>
                <p className="text-base font-semibold text-emerald-700 dark:text-emerald-300">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground mt-1">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
              </>
            ) : (
              <>
                <p className="text-base font-semibold text-foreground">
                  {isDragging ? 'Drop your file here' : 'Drag & drop your CSV file'}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  or <span className="text-primary font-medium">click to browse</span>
                </p>
              </>
            )}
          </div>

          <div className="text-xs text-muted-foreground space-y-0.5">
            <p>CSV files only · Maximum {maxSizeMB}MB</p>
          </div>
        </div>
      </div>

      {/* Selected file action */}
      {selectedFile && (
        <div className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2.5">
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
            <span className="font-medium truncate max-w-xs">{selectedFile.name}</span>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={clearFile}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}

      {/* Error */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
