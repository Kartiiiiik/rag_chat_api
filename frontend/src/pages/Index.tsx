import { FileText, MessageSquare, Sparkles } from 'lucide-react';
import { DocumentUpload } from '@/components/DocumentUpload';
import { ChatMessages } from '@/components/ChatMessages';
import { ChatInput } from '@/components/ChatInput';
import { useDocumentUpload } from '@/hooks/useDocumentUpload';
import { useChat } from '@/hooks/useChat';

const Index = () => {
  const {
    document,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    clearDocument,
  } = useDocumentUpload();

  const { messages, isLoading, sendMessage, clearMessages } = useChat();

  const handleSendMessage = async (content: string) => {
    await sendMessage(content, document);
  };

  const handleClearDocument = () => {
    clearDocument();
    clearMessages();
  };

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar / Document Panel */}
      <aside className="hidden w-80 flex-col border-r border-border bg-card lg:flex">
        <div className="flex h-16 items-center gap-3 border-b border-border px-6">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-bg">
            <Sparkles className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-semibold text-foreground">RAG Chat</h1>
            <p className="text-xs text-muted-foreground">Document Intelligence</p>
          </div>
        </div>

        <div className="flex-1 overflow-auto p-4 scrollbar-thin">
          <div className="space-y-4">
            <div>
              <h2 className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground">
                <FileText className="h-4 w-4" />
                Document
              </h2>
              <DocumentUpload
                document={document}
                isUploading={isUploading}
                uploadProgress={uploadProgress}
                error={error}
                onUpload={uploadDocument}
                onClear={handleClearDocument}
              />
            </div>

            {document && (
              <div className="animate-fade-in rounded-lg border border-border bg-background p-4">
                <h3 className="mb-2 text-sm font-medium text-foreground">Document Preview</h3>
                <p className="line-clamp-6 text-xs leading-relaxed text-muted-foreground">
                  {document.content.slice(0, 400)}
                  {document.content.length > 400 && '...'}
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-border p-4">
          <p className="text-center text-xs text-muted-foreground">
            Powered by RAG Technology
          </p>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex flex-1 flex-col">
        {/* Mobile Header */}
        <header className="flex h-16 items-center justify-between border-b border-border bg-card px-4 lg:hidden">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg gradient-bg">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <h1 className="font-semibold text-foreground">RAG Chat</h1>
          </div>
          
          {document && (
            <div className="flex items-center gap-2 rounded-lg bg-accent px-3 py-1.5">
              <FileText className="h-4 w-4 text-accent-foreground" />
              <span className="max-w-24 truncate text-xs font-medium text-accent-foreground">
                {document.name}
              </span>
            </div>
          )}
        </header>

        {/* Mobile Document Upload */}
        <div className="border-b border-border bg-card p-4 lg:hidden">
          <DocumentUpload
            document={document}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
            error={error}
            onUpload={uploadDocument}
            onClear={handleClearDocument}
          />
        </div>

        {/* Desktop Header */}
        <header className="hidden h-16 items-center justify-between border-b border-border bg-card px-6 lg:flex">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-muted-foreground" />
            <h2 className="font-medium text-foreground">Chat</h2>
            {messages.length > 0 && (
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {messages.length} messages
              </span>
            )}
          </div>
          
          {messages.length > 0 && (
            <button
              onClick={clearMessages}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear chat
            </button>
          )}
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-auto scrollbar-thin">
          <ChatMessages
            messages={messages}
            isLoading={isLoading}
            hasDocument={!!document}
          />
        </div>

        {/* Chat Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isLoading}
          placeholder={
            document
              ? 'Ask a question about your document...'
              : 'Upload a document first to start chatting...'
          }
        />
      </main>
    </div>
  );
};

export default Index;
