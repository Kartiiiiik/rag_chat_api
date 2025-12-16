export const API_BASE_URL = "/api/v1";

export interface DocumentResponse {
  id: number;
  filename: string;
  content: string;
  created_at: string;
  file_hash: string;
}

export interface ChatResponse {
  response: string;
  sources: Array<{
    document_id: number;
    content: string;
    chunk_index: number;
  }>;
}

export async function uploadDocument(file: File): Promise<DocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload document");
  }

  return response.json();
}

export async function chat(
  message: string,
  documentIds: number[],
  stream: boolean = false
): Promise<ChatResponse | ReadableStream<Uint8Array>> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      message,
      document_ids: documentIds,
      stream,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to send message");
  }

  if (stream) {
    return response.body!;
  }

  return response.json();
}
