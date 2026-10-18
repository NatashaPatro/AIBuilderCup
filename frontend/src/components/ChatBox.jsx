import { useState } from "react";
import { API_BASE_URL } from "../firebase";

export default function ChatBox({ alertId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const send = async () => {
    if (!input.trim()) return;
    const question = input.trim();
    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setSending(true);
    try {
      const res = await fetch(`${API_BASE_URL}/chat/${alertId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.answer }]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Something went wrong reaching the agent." },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="border-t border-slate-800 pt-4">
      <h3 className="font-medium text-sm mb-2 text-slate-300">
        Ask a follow-up question
      </h3>
      <div className="space-y-2 max-h-48 overflow-y-auto mb-3">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-sm rounded-lg px-3 py-2 max-w-[85%] ${
              m.role === "user"
                ? "bg-brand-accent/20 ml-auto text-right"
                : "bg-slate-800/60"
            }`}
          >
            {m.content}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="e.g. Why was the geo mismatch flagged?"
          className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-600 text-sm focus:outline-none focus:border-brand-accent"
        />
        <button
          onClick={send}
          disabled={sending}
          className="px-4 py-2 rounded-lg bg-brand-accent hover:bg-blue-500 text-sm font-medium disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}

