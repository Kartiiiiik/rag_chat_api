import { useState, useCallback } from 'react';
import { Document, SUPPORTED_TYPES, MAX_FILE_SIZE } from '@/types/chat';
import { parseDocument } from '@/services/documentParser';

interface UseDocumentUploadReturn {
  document: Document | null;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
  uploadDocument: (file: File) => Promise<void>;
  clearDocument: () => void;
}

export function useDocumentUpload(): UseDocumentUploadReturn {
  const [document, setDocument] = useState<Document | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): string | null => {
    const fileExtension = file.name.toLowerCase().split('.').pop();
    const isValidType = Object.keys(SUPPORTED_TYPES).includes(file.type) || 
                        (fileExtension && ['md', 'txt', 'pdf'].includes(fileExtension));
    
    if (!isValidType) {
      return 'Unsupported file type. Please upload PDF, TXT, or MD files.';
    }
    
    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds 10MB limit.';
    }
    
    return null;
  };

  const getFileType = (file: File): Document['type'] => {
    const extension = file.name.toLowerCase().split('.').pop();
    if (extension === 'md') return 'md';
    if (extension === 'txt') return 'txt';
    if (extension === 'pdf' || file.type === 'application/pdf') return 'pdf';
    return SUPPORTED_TYPES[file.type] || 'txt';
  };

  const uploadDocument = useCallback(async (file: File) => {
    setError(null);
    const validationError = validateFile(file);
    
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      const content = await parseDocument(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      const newDocument: Document = {
        id: crypto.randomUUID(),
        name: file.name,
        size: file.size,
        type: getFileType(file),
        content,
        uploadedAt: new Date(),
      };

      setDocument(newDocument);
      
      // Reset progress after a short delay
      setTimeout(() => setUploadProgress(0), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process document');
    } finally {
      setIsUploading(false);
    }
  }, []);

  const clearDocument = useCallback(() => {
    setDocument(null);
    setError(null);
    setUploadProgress(0);
  }, []);

  return {
    document,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    clearDocument,
  };
}
