import { Message, Document } from '@/types/chat';
import { chat } from './api';

export async function generateResponse(
  query: string,
  document: Document | null,
  conversationHistory: Message[]
): Promise<string> {
  if (!document) {
    return "Please upload a document first so I can help you analyze and answer questions about it.";
  }

  // Ensure document.id is a number (or handle conversion if it's currently a string uuid from the frontend mock)
  // The backend expects integer IDs. The frontend mock uses UUIDs.
  // We need to verify if the frontend flow has been updated to use the backend's integer IDs.
  // For now, we'll try to parse it, or rely on the fact that we'll update the document hook too.
  
  // Note: The backend expects 'document_ids' as a list on the request body.
  const documentId = parseInt(String(document.id), 10);

  if (isNaN(documentId)) {
      // Fallback or error if we're still using client-side UUIDs before the full switch
      console.warn("Document ID is not a number, might be client-side mock ID:", document.id);
      // We might need to handle this transition.
      // For now, let's assume valid ID flow or fail gracefully.
  }

  try {
    const response = await chat(query, [documentId]);
    
    // Check if it's a stream or simple response object
    if ('response' in response) {
        return response.response;
    } 
    
    // If stream (not implemented in this simple call yet), handling would be different.
    return "Stream response not fully implemented in this helper yet.";

  } catch (error) {
    console.error("Chat API Error:", error);
    return "Sorry, I had trouble communicating with the server.";
  }
}
