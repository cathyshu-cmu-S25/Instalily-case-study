export default function MessageList({ messages }) {
  return (
    <div className="message-list">
      {messages.map((msg, i) => (
        <div key={i} className={`message message--${msg.role}`}>
          <span className="message__label">
            {msg.role === "user" ? "You" : "PartSelect"}
          </span>
          <p className="message__text">{msg.content}</p>
        </div>
      ))}
    </div>
  );
}
