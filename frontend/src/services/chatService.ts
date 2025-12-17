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
  
  // Note: The backend expects 'document_ids' as a list on the request body.
  const documentId = parseInt(String(document.id), 10);

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
