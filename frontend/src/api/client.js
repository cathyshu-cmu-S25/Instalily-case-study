const BASE_URL = "http://localhost:8000";

export async function sendMessage(message, history = []) {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // { response, ui_block }
}
