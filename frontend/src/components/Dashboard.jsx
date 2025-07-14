import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const demoMetrics = {
  activeAgents: 5,
  tasksToday: 42,
  systemHealth: "Healthy",
  taskHistory: [
    { date: "Mon", tasks: 10 },
    { date: "Tue", tasks: 12 },
    { date: "Wed", tasks: 8 },
    { date: "Thu", tasks: 15 },
    { date: "Fri", tasks: 9 },
    { date: "Sat", tasks: 7 },
    { date: "Sun", tasks: 11 },
  ],
};

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    setMetrics(demoMetrics);
  }, []);

  if (!metrics) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Active Agents</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{metrics.activeAgents}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">Tasks Today</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{metrics.tasksToday}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm text-gray-500">System Health</div>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{metrics.systemHealth}</div>
        </div>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Task Completion (Last 7 Days)</h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={metrics.taskHistory}>
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="tasks" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
} 