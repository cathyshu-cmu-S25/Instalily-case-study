import { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import { sendMessage } from "../api/client";

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    const next = [...messages, userMsg];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const history = next.map((m) => ({ role: m.role, content: m.content }));
      const data = await sendMessage(text, history.slice(0, -1));
      setMessages([...next, { role: "assistant", content: data.response }]);
    } catch {
      setMessages([
        ...next,
        { role: "assistant", content: "Error: could not reach the server." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-window">
      <header className="chat-header">
        <span className="chat-header__logo">PartSelect</span>
        <span className="chat-header__subtitle">Parts Assistant</span>
      </header>

      <div className="chat-body">
        {messages.length === 0 && (
          <p className="chat-empty">
            Ask me about refrigerator or dishwasher parts.
          </p>
        )}
        <MessageList messages={messages} />
        {loading && <p className="chat-loading">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          rows={2}
          placeholder="Type a message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
        />
        <button className="chat-send" onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
