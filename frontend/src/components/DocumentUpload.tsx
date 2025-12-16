import React, { useCallback, useState } from 'react';
import { Upload, FileText, X, File, Loader2 } from 'lucide-react';
import { Document } from '@/types/chat';
import { cn } from '@/lib/utils';

interface DocumentUploadProps {
  document: Document | null;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  onUpload: (file: File) => Promise<void>;
  onClear: () => void;
}

export function DocumentUpload({
  document,
  isUploading,
  uploadProgress,
  error,
  onUpload,
  onClear,
}: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      await onUpload(file);
    }
  }, [onUpload]);

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await onUpload(file);
    }
    e.target.value = '';
  }, [onUpload]);

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (type: Document['type']) => {
    return <FileText className="h-5 w-5" />;
  };

  if (document) {
    return (
      <div className="animate-fade-in rounded-lg border border-border bg-card p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              {getFileIcon(document.type)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-card-foreground">{document.name}</p>
              <p className="text-sm text-muted-foreground">
                {formatFileSize(document.size)} • {document.type.toUpperCase()}
              </p>
            </div>
          </div>
          <button
            onClick={onClear}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Remove document"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={cn(
          "relative rounded-lg border-2 border-dashed p-8 text-center transition-all duration-200",
          isDragging
            ? "border-primary bg-upload-bg"
            : "border-border hover:border-upload-border hover:bg-upload-bg/50",
          isUploading && "pointer-events-none opacity-60"
        )}
      >
        <input
          type="file"
          accept=".pdf,.txt,.md,text/plain,text/markdown,application/pdf"
          onChange={handleFileSelect}
          className="absolute inset-0 cursor-pointer opacity-0"
          disabled={isUploading}
        />
        
        <div className="flex flex-col items-center gap-3">
          {isUploading ? (
            <Loader2 className="h-10 w-10 animate-spin text-primary" />
          ) : (
            <div className="rounded-full bg-accent p-3">
              <Upload className="h-6 w-6 text-accent-foreground" />
            </div>
          )}
          
          <div>
            <p className="font-medium text-foreground">
              {isUploading ? 'Processing document...' : 'Drop your document here'}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {isUploading 
                ? `${uploadProgress}% complete`
                : 'or click to browse • PDF, TXT, MD up to 10MB'
              }
            </p>
          </div>
        </div>

        {isUploading && uploadProgress > 0 && (
          <div className="mt-4">
            <div className="h-1.5 overflow-hidden rounded-full bg-muted">
              <div
                className="gradient-bg h-full transition-all duration-300 ease-out"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="animate-fade-in rounded-lg bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}
    </div>
  );
}
