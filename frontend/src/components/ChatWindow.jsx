import { useState, useRef, useEffect } from "react";
import MessageList from "./MessageList";
import { streamMessage } from "../api/client";

const WELCOME_MSG = {
  role: "assistant",
  content: "Hi! I can help you with refrigerator and dishwasher parts. What can I help you with today?",
  ui_blocks: [],
  streaming: false,
  isWelcome: true,
};

const WELCOME_OPTIONS = [
  "Look up a part",
  "Find parts for my model",
  "Check compatibility",
  "Get installation help",
  "Troubleshoot a symptom",
  "Check order status",
];

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
  const chips = CHIPS[lastBlock?.type] || [];
  const ps = lastBlock?.data?.part?.ps_number ?? lastBlock?.data?.ps_number;
  if (!ps) return chips;
  return chips.map((c) => {
    if (c === "Add to cart" || c === "Add this part to cart") return `Add ${ps} to cart`;
    if (c === "How do I install this?") return `How do I install ${ps}?`;
    if (c === "Is this compatible with my model?") return `Is ${ps} compatible with my model?`;
    return c;
  });
}

export default function ChatWindow() {
  const [messages, setMessages] = useState([WELCOME_MSG]);
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

    const history = messages
      .filter((m) => !m.isWelcome)
      .map((m) => ({ role: m.role, content: m.content, ui_blocks: m.ui_blocks ?? [] }));
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
        <MessageList messages={messages} />
        {messages.length === 1 && messages[0].isWelcome && !loading && (
          <div className="chat-welcome__options">
            {WELCOME_OPTIONS.map((opt) => (
              <button key={opt} className="welcome-option" onClick={() => handleSend(opt)}>
                {opt}
              </button>
            ))}
          </div>
        )}
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
