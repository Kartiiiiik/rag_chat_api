import { Message, Document } from '@/types/chat';

// Simulated RAG response - in production, this would call your backend API
export async function generateResponse(
  query: string,
  document: Document | null,
  conversationHistory: Message[]
): Promise<string> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));

  if (!document) {
    return "Please upload a document first so I can help you analyze and answer questions about it. I support PDF, TXT, and Markdown files.";
  }

  // Simple keyword-based response simulation
  // In production, this would use actual RAG with embeddings and LLM
  const queryLower = query.toLowerCase();
  const documentContent = document.content.toLowerCase();
  
  // Check if query relates to document content
  const queryWords = queryLower.split(/\s+/).filter(word => word.length > 3);
  const relevantSentences: string[] = [];
  
  const sentences = document.content.split(/[.!?]+/).filter(s => s.trim());
  
  for (const sentence of sentences) {
    const sentenceLower = sentence.toLowerCase();
    if (queryWords.some(word => sentenceLower.includes(word))) {
      relevantSentences.push(sentence.trim());
    }
  }

  if (relevantSentences.length > 0) {
    const context = relevantSentences.slice(0, 3).join('. ');
    return `Based on the document "${document.name}", here's what I found:\n\n${context}.\n\nWould you like me to elaborate on any specific aspect?`;
  }

  // Generic responses based on query type
  if (queryLower.includes('summary') || queryLower.includes('summarize')) {
    const preview = document.content.slice(0, 500);
    return `Here's a summary of "${document.name}":\n\nThe document contains ${document.content.split(/\s+/).length} words. ${preview}...\n\nWould you like me to focus on a specific section?`;
  }

  if (queryLower.includes('what') || queryLower.includes('explain')) {
    return `I've analyzed "${document.name}" but couldn't find specific information matching your query. The document appears to cover: ${document.content.slice(0, 200)}...\n\nCould you rephrase your question or ask about specific topics from the document?`;
  }

  return `I've searched through "${document.name}" but couldn't find a direct answer to your question. Here's what the document covers:\n\n${document.content.slice(0, 300)}...\n\nTry asking about specific topics mentioned in the document.`;
}
