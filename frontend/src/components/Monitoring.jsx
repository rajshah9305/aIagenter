import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const demoData = {
  metrics: [
    { time: "10:00", cpu: 20, memory: 40 },
    { time: "11:00", cpu: 35, memory: 50 },
    { time: "12:00", cpu: 30, memory: 45 },
    { time: "13:00", cpu: 50, memory: 60 },
    { time: "14:00", cpu: 40, memory: 55 },
  ],
};

export default function Monitoring() {
  const [data, setData] = useState(null);

  useEffect(() => {
    setData(demoData);
  }, []);

  if (!data) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Monitoring</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">System Metrics</h2>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data.metrics}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="cpu" stroke="#3b82f6" />
            <Line type="monotone" dataKey="memory" stroke="#10b981" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
} 