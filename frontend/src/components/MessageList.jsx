import CARD_REGISTRY from "./cards/index";

export default function MessageList({ messages }) {
  return (
    <div className="message-list">
      {messages.map((msg, i) => (
        <div key={i} className={`message message--${msg.role}`}>
          <span className="message__label">
            {msg.role === "user" ? "You" : "PartSelect"}
          </span>

          {/* Text bubble — always shown when there's content */}
          {msg.content && (
            <p className="message__text">
              {msg.content}
              {msg.streaming && <span className="message__cursor" />}
            </p>
          )}

          {/* Typed UI block — rendered after streaming completes */}
          {!msg.streaming && msg.ui_block && (() => {
            const Card = CARD_REGISTRY[msg.ui_block.type];
            return Card ? <Card data={msg.ui_block.data} /> : null;
          })()}
        </div>
      ))}
    </div>
  );
}
