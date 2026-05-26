import ReactMarkdown from "react-markdown";
import CARD_REGISTRY from "./cards/index";

export default function MessageList({ messages }) {
  return (
    <div className="message-list">
      {messages.map((msg, i) => (
        <div key={i} className={`message message--${msg.role}`}>
          <span className="message__label">
            {msg.role === "user" ? "You" : "PartSelect"}
          </span>

          {/* Text bubble — hidden once a card is ready */}
          {(msg.streaming || !msg.ui_block) && (msg.content || msg.streaming) && (
            <div className="message__text">
              {msg.streaming && !msg.content
                ? <span className="message__thinking">Thinking<span className="message__dots" /></span>
                : <ReactMarkdown>{msg.content}</ReactMarkdown>
              }
              {msg.streaming && msg.content && <span className="message__cursor" />}
            </div>
          )}

          {/* Typed UI block — rendered only after streaming completes */}
          {!msg.streaming && msg.ui_block && (() => {
            const Card = CARD_REGISTRY[msg.ui_block.type];
            return Card ? <Card data={msg.ui_block.data} /> : null;
          })()}
        </div>
      ))}
    </div>
  );
}
