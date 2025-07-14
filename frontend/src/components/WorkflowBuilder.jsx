import React, { useCallback } from "react";
import ReactFlow, { MiniMap, Controls, Background, useNodesState, useEdgesState, addEdge } from "reactflow";
import "reactflow/dist/style.css";

const initialNodes = [
  { id: "1", type: "input", data: { label: "Start" }, position: { x: 0, y: 50 } },
  { id: "2", data: { label: "Agent Task" }, position: { x: 200, y: 100 } },
  { id: "3", type: "output", data: { label: "End" }, position: { x: 400, y: 50 } },
];
const initialEdges = [
  { id: "e1-2", source: "1", target: "2" },
  { id: "e2-3", source: "2", target: "3" },
];

export default function WorkflowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  return (
    <div className="p-8 h-[80vh]">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Workflow Builder</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>
    </div>
  );
} 