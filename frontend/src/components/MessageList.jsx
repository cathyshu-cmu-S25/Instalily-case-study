import ReactMarkdown from "react-markdown";
import CARD_REGISTRY from "./cards/index";

export default function MessageList({ messages, onSend }) {
  return (
    <div className="message-list">
      {messages.map((msg, i) => (
        <div key={i} className={`message message--${msg.role}`}>
          <span className="message__label">
            {msg.role === "user" ? "You" : "PartSelect"}
          </span>

          {/* Text bubble — hidden once cards are ready, except for install_guide which adds context */}
          {(msg.streaming || !msg.ui_blocks?.length || msg.ui_blocks?.some(b => b.type === "install_guide")) && (msg.content || msg.streaming) && (
            <div className="message__text">
              {msg.streaming && !msg.content
                ? <span className="message__thinking">Thinking<span className="message__dots" /></span>
                : <ReactMarkdown>{msg.content}</ReactMarkdown>
              }
              {msg.streaming && msg.content && <span className="message__cursor" />}
            </div>
          )}

          {/* UI cards — all rendered after streaming completes */}
          {!msg.streaming && msg.ui_blocks?.map((block, j) => {
            const Card = CARD_REGISTRY[block.type];
            return Card ? <Card key={j} data={block.data} onSend={onSend} /> : null;
          })}
        </div>
      ))}
    </div>
  );
}
