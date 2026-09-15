export interface ChatRequest {
    question: string;
    history?: {
        role: string;
        content: string;
    }[];
}

export interface RetrievedDocument {
    source?: string;
    source_file?: string;
    relative_path?: string;
    page?: number;
    chunk?: number;
    content?: string;
  }

export interface ChatResponse {
    answer: string;
    documents?: RetrievedDocument[];
    request_id?: string;
    retrieved_time?: number;
    generation_time?: number;
    total_time?: number;
    num_documents?: number;
}

export interface StreamEvent {
    event: string;
    data: unknown;
  }

  
export interface StreamDoneData {
status?: string;
request_id?: string;
documents_found?: number;
retrieval_time?: number;
generation_time?: number;
}