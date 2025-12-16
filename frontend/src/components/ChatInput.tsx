import React, { useState, useCallback, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, disabled, placeholder = 'Ask a question about your document...' }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = useCallback(() => {
    if (input.trim() && !disabled) {
      onSend(input);
      setInput('');
    }
  }, [input, disabled, onSend]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <div className="border-t border-border bg-card p-4">
      <div className="flex items-end gap-3">
        <div className="relative flex-1">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "max-h-32 min-h-[44px] w-full resize-none rounded-xl border border-input bg-background px-4 py-3 pr-12 text-sm text-foreground placeholder:text-muted-foreground",
              "focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20",
              "disabled:cursor-not-allowed disabled:opacity-50",
              "transition-all duration-200"
            )}
            style={{
              height: 'auto',
              minHeight: '44px',
            }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = `${Math.min(target.scrollHeight, 128)}px`;
            }}
          />
        </div>
        
        <button
          onClick={handleSend}
          disabled={disabled || !input.trim()}
          className={cn(
            "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-all duration-200",
            input.trim() && !disabled
              ? "gradient-bg text-primary-foreground hover:opacity-90 active:scale-95"
              : "bg-muted text-muted-foreground cursor-not-allowed"
          )}
          aria-label="Send message"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
      
      <p className="mt-2 text-center text-xs text-muted-foreground">
        Press Enter to send • Shift+Enter for new line
      </p>
    </div>
  );
}
