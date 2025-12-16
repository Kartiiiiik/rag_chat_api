import React, { useRef, useEffect } from 'react';
import { Message } from '@/types/chat';
import { ChatMessage } from './ChatMessage';
import { MessageSquare, Loader2 } from 'lucide-react';

interface ChatMessagesProps {
  messages: Message[];
  isLoading: boolean;
  hasDocument: boolean;
}

export function ChatMessages({ messages, isLoading, hasDocument }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center px-4 text-center">
        <div className="rounded-full bg-accent p-4">
          <MessageSquare className="h-8 w-8 text-accent-foreground" />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-foreground">
          {hasDocument ? 'Ready to chat!' : 'No document loaded'}
        </h3>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">
          {hasDocument
            ? 'Ask me anything about your document. I can summarize, explain, or find specific information.'
            : 'Upload a document to start asking questions. I support PDF, TXT, and Markdown files.'}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      
      {isLoading && (
        <div className="flex gap-3 animate-fade-in">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
            <Loader2 className="h-4 w-4 animate-spin text-secondary-foreground" />
          </div>
          <div className="flex items-center rounded-2xl rounded-bl-md bg-chat-assistant px-4 py-2.5">
            <div className="flex gap-1">
              <span className="h-2 w-2 animate-pulse-soft rounded-full bg-muted-foreground" style={{ animationDelay: '0ms' }} />
              <span className="h-2 w-2 animate-pulse-soft rounded-full bg-muted-foreground" style={{ animationDelay: '150ms' }} />
              <span className="h-2 w-2 animate-pulse-soft rounded-full bg-muted-foreground" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}
      
      <div ref={bottomRef} />
    </div>
  );
}
