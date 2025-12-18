export async function parseDocument(file: File): Promise<string> {
  const extension = file.name.toLowerCase().split('.').pop();

  if (extension === 'pdf' || file.type === 'application/pdf') {
    return `[PDF Document: ${file.name}]\n\nThis is a PDF file. For full PDF text extraction, connect to Lovable Cloud to process documents server-side.\n\nFor now, please upload TXT or MD files for full text analysis.`;
  }
  
  // For text and markdown files, read as text
  return await file.text();
}
