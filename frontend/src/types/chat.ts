export interface Document {
  id: string;
  name: string;
  size: number;
  type: 'pdf' | 'txt' | 'md';
  content: string;
  uploadedAt: Date;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  document: Document | null;
}

export type SupportedFileType = 'application/pdf' | 'text/plain' | 'text/markdown';

export const SUPPORTED_TYPES: Record<string, Document['type']> = {
  'application/pdf': 'pdf',
  'text/plain': 'txt',
  'text/markdown': 'md',
  '.md': 'md',
};

export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
