import { useEffect, useState, useRef, type SubmitEvent,  } from "react";

import { streamChatMessage } from "../api/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWindowProps {
    onSessionExpired: () => void;
  }

export default function ChatWindow({
    onSessionExpired,
  }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Whenever messages change, scroll to the
  // newest content. This also works while
  // tokens are streaming.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function handleSubmit(
    event: SubmitEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const question = input.trim();

    if (!question || loading) {
      return;
    }

    const previousMessages = messages;

    const userMessage: Message = {
      role: "user",
      content: question,
    };

    const updatedMessages = [
      ...previousMessages,
      userMessage,
    ];

    setMessages(updatedMessages);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const assistantMessage: Message = {
        role: "assistant",
        content: "",
      };

      setMessages([
        ...updatedMessages,
        assistantMessage,
      ]);

      
      await streamChatMessage(
        {
          question,
          history: previousMessages,
        },
        (token) => {
          if (typeof token !== "string") {
            return;
          }

          setMessages((currentMessages) => {
            const nextMessages = [
              ...currentMessages,
            ];

            const lastIndex =
              nextMessages.length - 1;

            const lastMessage =
              nextMessages[lastIndex];

            if (
              lastMessage &&
              lastMessage.role === "assistant"
            ) {
              nextMessages[lastIndex] = {
                ...lastMessage,
                content:
                  lastMessage.content + token,
              };
            }

            return nextMessages;
          });
        }
      );
      
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Something went wrong";
    
      if (message === "Session expired") {
        onSessionExpired();
        return;
      }

      setError(message);

      setMessages((currentMessages) => {
        const nextMessages = [
          ...currentMessages,
        ];

        const lastIndex =
          nextMessages.length - 1;

        const lastMessage =
          nextMessages[lastIndex];

        if (
          lastMessage &&
          lastMessage.role === "assistant" &&
          lastMessage.content === ""
        ) {
          nextMessages.pop();
        }

        return nextMessages;
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Chat</h2>
      </div>
  
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>
              Ask a question about your documents.
            </p>
          </div>
        )}
  
        {messages.map((message, index) => (
          <div
            key={index}
            className={`message-row ${message.role}`}
          >
            <div className="message-bubble">
              <span className="message-label">
                {message.role === "user"
                  ? "You"
                  : "Assistant"}
              </span>
  
              {message.content ? (
                message.content
              ) : (
                message.role === "assistant" &&
                loading && (
                  <span className="generating-text">
                    Generating...
                  </span>
                )
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
  
      {error && (
        <p className="chat-error">
          {error}
        </p>
      )}
  
      <form
        className="chat-input-area"
        onSubmit={handleSubmit}
      >
        <input
          className="chat-input"
          type="text"
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          placeholder="Ask a question..."
          disabled={loading}
        />
  
        <button
          className="send-button"
          type="submit"
          disabled={
            loading || !input.trim()
          }
        >
          {loading
            ? "Generating..."
            : "Send"}
        </button>
      </form>
    </div>
  );
}

/*
  return (
    <div>
      <h2>Chat</h2>

      <div>
        <h3>Conversation</h3>

        {messages.length === 0 && (
          <p>
            Your conversation will appear here.
          </p>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <strong>
              {message.role === "user"
                ? "You"
                : "Assistant"}
            </strong>

            <p
              style={{
                whiteSpace: "pre-wrap",
              }}
            >
              {message.content ||
                (
                  message.role === "assistant" &&
                  loading
                    ? "Generating..."
                    : ""
                )}
            </p>
          </div>
        ))}
      </div>

      {error && (
        <p>
          Error: {error}
        </p>
      )}

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          placeholder="Ask a question..."
          disabled={loading}
        />

        <button
          type="submit"
          disabled={
            loading || !input.trim()
          }
        >
          {loading
            ? "Generating..."
            : "Send"}
        </button>
      </form>
    </div>
  );
*/