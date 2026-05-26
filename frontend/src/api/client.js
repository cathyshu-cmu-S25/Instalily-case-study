const BASE_URL = "http://localhost:8000";

export async function sendMessage(message, history = []) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/**
 * Stream a chat message via SSE.
 * @param {string} message
 * @param {Array} history
 * @param {(delta: string) => void} onDelta  — called for each text chunk
 * @param {(ui_blocks: object[]) => void} onDone — called once when stream ends
 */
export async function streamMessage(message, history = [], onDelta, onDone) {
  const res = await fetch(`${BASE_URL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop(); // keep any incomplete trailing line

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        const event = JSON.parse(line.slice(6));
        if (event.type === "text_delta") onDelta(event.content);
        else if (event.type === "done") onDone(event.ui_blocks ?? []);
      } catch {
        // skip malformed event
      }
    }
  }
}
