import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, MessageSquare, Sparkles, LogOut, User } from 'lucide-react';
import { DocumentUpload } from '@/components/DocumentUpload';
import { ChatMessages } from '@/components/ChatMessages';
import { ChatInput } from '@/components/ChatInput';
import { ThemeToggle } from '@/components/ThemeToggle';
import { useDocumentUpload } from '@/hooks/useDocumentUpload';
import { useChat } from '@/hooks/useChat';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const Index = () => {
  const { user, isLoading: authLoading, logout } = useAuth();
  const navigate = useNavigate();

  const {
    document,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    clearDocument,
  } = useDocumentUpload();

  const { messages, isLoading, sendMessage, clearMessages } = useChat();

  useEffect(() => {
    if (!authLoading && !user) {
      navigate('/auth');
    }
  }, [user, authLoading, navigate]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content, document);
  };

  const handleClearDocument = () => {
    clearDocument();
    clearMessages();
  };

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!user) return null;

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
          
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9">
                  <User className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
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
          
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear chat
              </button>
            )}
            <ThemeToggle />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="gap-2">
                  <User className="h-4 w-4" />
                  <span className="max-w-32 truncate">{user.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <div className="px-2 py-1.5">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
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
