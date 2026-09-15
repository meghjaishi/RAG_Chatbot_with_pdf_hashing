import type {ChatRequest, ChatResponse, StreamEvent} from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function sendChatMessage(
request: ChatRequest
): Promise<ChatResponse> {
    const token =
      sessionStorage.getItem("access_token");
  
    if (!token) {
      throw new Error("Not authenticated");
    }
  
    const response = await fetch(
      `${API_BASE_URL}/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(request),
      }
    );
  
    if (response.status === 401) {
      sessionStorage.removeItem(
        "access_token"
      );
  
      throw new Error("Session expired");
    }
  
    if (!response.ok) {
      const errorBody =
        await response.text();
  
      throw new Error(
        `Chat request failed: ` +
        `${response.status} ${errorBody}`
      );
    }
  
    return response.json();
}
  

export async function streamChatMessage(
    request: ChatRequest,
    onEvent: (event: StreamEvent) => void
): Promise<void> {
    const token = sessionStorage.getItem("access_token");
  
    if (!token) {
      throw new Error("Not authenticated");
    }
  
    const response = await fetch(
      `${API_BASE_URL}/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(request),
      }
    );
  
    if (response.status === 401) {
      sessionStorage.removeItem(
        "access_token"
      );
  
      throw new Error("Session expired");
    }
  
    if (!response.ok) {
      const errorBody = await response.text();
  
      throw new Error(
        `Streaming request failed: ` +
        `${response.status} ${errorBody}`
      );
    }
  
    if (!response.body) {
      throw new Error(
        "Streaming response body is unavailable"
      );
    }
  
    const reader = response.body.getReader();
  
    const decoder = new TextDecoder();
  
    let buffer = "";
  
    while (true) {
      const { value, done,
      } = await reader.read();
  
      if (done) {
        break;
      }
  
      buffer += decoder.decode(
        value,
        { stream: true }
      );

      const events = buffer.split("\n\n");
  
      buffer = events.pop() ?? "";
  
      for (const rawEvent of events) {
        processSSEEvent(rawEvent, onEvent);
      }
    }
  
    buffer += decoder.decode();

    if (buffer.trim()) {
      processSSEEvent(buffer, onEvent);
    }
}

function processSSEEvent(
    rawEvent: string,
    onEvent: (event: StreamEvent) => void
  ): void {
    const lines = rawEvent.split("\n");
  
    let eventName = "";
    let rawData = "";
  
    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line
          .slice(6)
          .trim();
      }
  
      if (line.startsWith("data:")) {
        rawData = line
          .slice(5)
          .trim();
      }
    }
  
    if (!eventName || !rawData) {
      return;
    }
  
    try {
      const parsedData: unknown =
        JSON.parse(rawData);
  
      onEvent({
        event: eventName,
        data: parsedData,
      });
    } catch {
      console.warn(
        "Could not parse SSE event:",
        rawEvent
      );
    }
  }

/*
function processSSEEvent(
    rawEvent: string,
    onEvent: (event: StreamEvent) => void
  ): void {
    const lines = rawEvent.split("\n");
  
    for (const line of lines) {
      if (!line.startsWith("data:")) {
        continue;
      }
  
      const rawData = line
        .slice(5)
        .trim();
  
      if (!rawData) {
        continue;
      }
  
      try {
        const parsedEvent =
          JSON.parse(rawData) as StreamEvent;
  
        onEvent(parsedEvent);
      } catch {
        console.warn(
          "Could not parse SSE event:",
          rawData
        );
      }
    }
}
*/