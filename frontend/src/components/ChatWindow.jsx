import { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import { streamMessage } from "../api/client";

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
  const lastBlock = lastMsg.ui_blocks?.[lastMsg.ui_blocks.length - 1];
  return CHIPS[lastBlock?.type] || [];
}

export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    text = (text ?? input).trim();
    if (!text || loading) return;

    setInput("");
    setError(null);
    setLoading(true);

    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    const withUser = [...messages, { role: "user", content: text }];

    setMessages([
      ...withUser,
      { role: "assistant", content: "", ui_blocks: [], streaming: true },
    ]);

    let accumulated = "";

    try {
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
              ui_blocks: [],
              streaming: true,
            };
            return next;
          });
        },
        (ui_blocks) => {
          setMessages((prev) => {
            const next = [...prev];
            next[next.length - 1] = {
              role: "assistant",
              content: accumulated,
              ui_blocks,
              streaming: false,
            };
            return next;
          });
          setLoading(false);
        }
      );
    } catch (err) {
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = {
          role: "assistant",
          content: "Sorry, I couldn't reach the server. Please check your connection and try again.",
          ui_block: null,
          streaming: false,
        };
        return next;
      });
      setError("Connection error");
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
  const inputTrimmed = input.trim();

  return (
    <div className="chat-window">
      <header className="chat-header">
        <span className="chat-header__logo">PartSelect</span>
        <span className="chat-header__subtitle">Parts Assistant</span>
      </header>

      <div className="chat-body">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask me about refrigerator or dishwasher parts.</p>
            <p className="chat-empty__hint">Part lookup · Compatibility · Installation · Troubleshooting</p>
          </div>
        )}
        <MessageList messages={messages} />
        <div ref={bottomRef} />
      </div>

      {chips.length > 0 && !loading && (
        <div className="chat-chips">
          {chips.map((chip) => (
            <button key={chip} className="chip" onClick={() => handleSend(chip)}>
              {chip}
            </button>
          ))}
        </div>
      )}

      {error && <p className="chat-error">{error}</p>}

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
        <button
          className="chat-send"
          onClick={() => handleSend()}
          disabled={loading || !inputTrimmed}
        >
          {loading ? "…" : "Send"}
        </button>
      </div>
    </div>
  );
}
