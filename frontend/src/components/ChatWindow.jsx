import { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import { streamMessage } from "../api/client";

// Static follow-up chips per ui_block type
const CHIPS = {
  product_card: ["How do I install this?", "Is this compatible with my model?", "Add to cart"],
  compatibility_result: ["Show me the installation guide", "What other parts fit my model?"],
  install_guide: ["Add this part to cart", "Check compatibility with my model"],
  troubleshoot_result: ["How do I install the recommended part?", "Add recommended parts to cart"],
  order_card: ["I need to return an item"],
  cart_confirmation: ["Check order status", "What else do I need?"],
};

function getChips(lastMsg) {
  if (!lastMsg || lastMsg.role !== "assistant" || lastMsg.streaming) return [];
  return CHIPS[lastMsg.ui_block?.type] || [];
}

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    text = (text ?? input).trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);

    const userMsg = { role: "user", content: text };
    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    // Add user message + empty streaming assistant placeholder
    const withUser = [...messages, userMsg];
    setMessages([...withUser, { role: "assistant", content: "", ui_block: null, streaming: true }]);

    try {
      let accumulated = "";
      await streamMessage(
        text,
        history,
        (delta) => {
          accumulated += delta;
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: accumulated,
              ui_block: null,
              streaming: true,
            };
            return next;
          });
        },
        (ui_block) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: accumulated,
              ui_block,
              streaming: false,
            };
            return next;
          });
          setLoading(false);
        }
      );
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: "Sorry, something went wrong. Please try again.",
          ui_block: null,
          streaming: false,
        };
        return next;
      });
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const chips = getChips(messages[messages.length - 1]);

  return (
    <div className="chat-window">
      <header className="chat-header">
        <span className="chat-header__logo">PartSelect</span>
        <span className="chat-header__subtitle">Parts Assistant</span>
      </header>

      <div className="chat-body">
        {messages.length === 0 && (
          <p className="chat-empty">Ask me about refrigerator or dishwasher parts.</p>
        )}
        <MessageList messages={messages} />
        {loading && messages[messages.length - 1]?.streaming === false && (
          <p className="chat-loading">Thinking…</p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Follow-up chips */}
      {chips.length > 0 && !loading && (
        <div className="chat-chips">
          {chips.map((chip) => (
            <button key={chip} className="chip" onClick={() => handleSend(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}

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
        <button className="chat-send" onClick={() => handleSend()} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}
