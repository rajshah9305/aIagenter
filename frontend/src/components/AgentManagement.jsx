import React, { useEffect, useState } from "react";

const demoAgents = [
  { id: 1, name: "Agent Alpha", framework: "AutoGen", status: "Active" },
  { id: 2, name: "Agent Beta", framework: "CrewAI", status: "Paused" },
  { id: 3, name: "Agent Gamma", framework: "MetaGPT", status: "Inactive" },
];

export default function AgentManagement() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAgents(demoAgents);
    setLoading(false);
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Agent Management</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <table className="min-w-full">
          <thead>
            <tr>
              <th className="text-left py-2 px-4">Name</th>
              <th className="text-left py-2 px-4">Framework</th>
              <th className="text-left py-2 px-4">Status</th>
              <th className="text-left py-2 px-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.id} className="border-t border-gray-200 dark:border-gray-700">
                <td className="py-2 px-4">{agent.name}</td>
                <td className="py-2 px-4">{agent.framework}</td>
                <td className="py-2 px-4">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    agent.status === "Active"
                      ? "bg-green-100 text-green-700"
                      : agent.status === "Paused"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-gray-200 text-gray-700"
                  }`}>
                    {agent.status}
                  </span>
                </td>
                <td className="py-2 px-4">
                  <button className="text-blue-600 hover:underline mr-2">Edit</button>
                  <button className="text-red-600 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 