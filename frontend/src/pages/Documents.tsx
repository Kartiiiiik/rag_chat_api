import { useEffect, useState } from 'react';
import { ArrowLeft, FileText, Trash2, Loader2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDocuments, deleteDocument, DocumentResponse } from '@/services/api';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const Documents = () => {
    const [documents, setDocuments] = useState<DocumentResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isDeleting, setIsDeleting] = useState<number | null>(null);

    const fetchDocuments = async () => {
        try {
            const data = await getDocuments();
            setDocuments(data);
        } catch (error) {
            toast.error("Failed to load documents");
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this document?")) return;
        
        setIsDeleting(id);
        try {
            await deleteDocument(id);
            setDocuments(documents.filter(doc => doc.id !== id));
            toast.success("Document deleted");
        } catch (error) {
            toast.error("Failed to delete document");
        } finally {
            setIsDeleting(null);
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="flex min-h-screen bg-background bg-gradient-to-br from-background via-background to-accent/5">
            {/* Sidebar (simplified/reused part of layout) */}
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
                <div className="p-4">
                     <Link to="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Chat
                    </Link>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 p-8">
                <div className="mx-auto max-w-4xl space-y-8">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-foreground">Documents</h2>
                            <p className="text-muted-foreground">Manage your uploaded knowledge base</p>
                        </div>
                        <Link to="/" className="flex items-center gap-2 lg:hidden text-sm text-muted-foreground">
                             <ArrowLeft className="h-4 w-4" /> Back
                        </Link>
                    </div>

                    {isLoading ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center animate-fade-in">
                            <div className="rounded-full bg-muted p-4 mb-4">
                                <FileText className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <h3 className="text-lg font-semibold">No documents yet</h3>
                            <p className="text-sm text-muted-foreground mb-4">Upload documents in the chat interface to see them here.</p>
                            <Link to="/">
                                <Button>Go to Chat</Button>
                            </Link>
                        </div>
                    ) : (
                        <div className="rounded-xl border bg-card text-card-foreground shadow-sm animate-fade-in">
                            <div className="relative w-full overflow-auto">
                                <table className="w-full caption-bottom text-sm">
                                    <thead className="[&_tr]:border-b">
                                        <tr className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Name</th>
                                            <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Uploaded</th>
                                            <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="[&_tr:last-child]:border-0">
                                        {documents.map((doc) => (
                                            <tr key={doc.id} className="border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted">
                                                <td className="p-4 align-middle font-medium">
                                                    <div className="flex items-center gap-2">
                                                        <FileText className="h-4 w-4 text-primary" />
                                                        {doc.filename}
                                                    </div>
                                                </td>
                                                <td className="p-4 align-middle text-muted-foreground">
                                                    {formatDate(doc.created_at)}
                                                </td>
                                                <td className="p-4 align-middle text-right">
                                                    <Button 
                                                        variant="ghost" 
                                                        size="icon"
                                                        onClick={() => handleDelete(doc.id)}
                                                        disabled={isDeleting === doc.id}
                                                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    >
                                                        {isDeleting === doc.id ? (
                                                            <Loader2 className="h-4 w-4 animate-spin" />
                                                        ) : (
                                                            <Trash2 className="h-4 w-4" />
                                                        )}
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default Documents;
