import React, { useEffect, useState } from "react";
// import { useSocket } from "../hooks/useSocket";

export default function Communication() {
  const [messages, setMessages] = useState([
    "Welcome to the agent chat!",
    "Agent Alpha: Task completed.",
    "Agent Beta: Awaiting instructions.",
  ]);
  const [input, setInput] = useState("");
  // const socket = useSocket();

  // useEffect(() => {
  //   socket.on("message", (msg) => setMessages((m) => [...m, msg]));
  //   return () => socket.off("message");
  // }, [socket]);

  const sendMessage = () => {
    if (input.trim()) {
      setMessages((m) => [...m, `You: ${input}`]);
      setInput("");
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Communication</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 h-96 overflow-y-auto mb-4">
        {messages.map((msg, i) => (
          <div key={i} className="mb-2 text-gray-800 dark:text-gray-200">{msg}</div>
        ))}
      </div>
      <div className="flex">
        <input
          className="flex-1 rounded-l px-4 py-2 border-t border-b border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          className="rounded-r px-4 py-2 bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
          onClick={sendMessage}
        >
          Send
        </button>
      </div>
    </div>
  );
} 