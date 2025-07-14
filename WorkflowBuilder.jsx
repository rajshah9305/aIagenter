import { useState, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  Plus, 
  Play, 
  Save, 
  Download, 
  Upload,
  Trash2,
  Settings,
  ArrowRight,
  GitBranch,
  Circle,
  Square
} from 'lucide-react'

export default function WorkflowBuilder() {
  const [workflows, setWorkflows] = useState([
    {
      id: 'workflow-1',
      name: 'Research & Analysis Pipeline',
      description: 'Automated research and analysis workflow using multiple agents',
      status: 'active',
      created: '2024-01-15',
      lastRun: '2 hours ago',
      nodes: [
        { id: 'node-1', type: 'agent', name: 'Data Collector', framework: 'CrewAI', x: 100, y: 100 },
        { id: 'node-2', type: 'agent', name: 'Analyzer', framework: 'AutoGen', x: 300, y: 100 },
        { id: 'node-3', type: 'agent', name: 'Report Generator', framework: 'LangGraph', x: 500, y: 100 }
      ],
      connections: [
        { from: 'node-1', to: 'node-2' },
        { from: 'node-2', to: 'node-3' }
      ]
    },
    {
      id: 'workflow-2',
      name: 'Content Creation Flow',
      description: 'Multi-agent content creation and review process',
      status: 'draft',
      created: '2024-01-12',
      lastRun: 'Never',
      nodes: [
        { id: 'node-1', type: 'agent', name: 'Content Writer', framework: 'MetaGPT', x: 100, y: 100 },
        { id: 'node-2', type: 'agent', name: 'Editor', framework: 'AutoGen', x: 300, y: 100 },
        { id: 'node-3', type: 'condition', name: 'Quality Check', x: 500, y: 100 },
        { id: 'node-4', type: 'agent', name: 'Publisher', framework: 'CrewAI', x: 700, y: 100 }
      ],
      connections: [
        { from: 'node-1', to: 'node-2' },
        { from: 'node-2', to: 'node-3' },
        { from: 'node-3', to: 'node-4' }
      ]
    }
  ])

  const [selectedWorkflow, setSelectedWorkflow] = useState(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newWorkflow, setNewWorkflow] = useState({
    name: '',
    description: ''
  })

  const [canvasNodes, setCanvasNodes] = useState([])
  const [canvasConnections, setCanvasConnections] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)

  const availableAgents = [
    { id: 'agent-1', name: 'AutoGen Assistant', framework: 'AutoGen' },
    { id: 'agent-2', name: 'CrewAI Researcher', framework: 'CrewAI' },
    { id: 'agent-3', name: 'LangGraph Processor', framework: 'LangGraph' },
    { id: 'agent-4', name: 'MetaGPT Planner', framework: 'MetaGPT' }
  ]

  const nodeTypes = [
    { type: 'agent', label: 'Agent', icon: Circle },
    { type: 'condition', label: 'Condition', icon: GitBranch },
    { type: 'action', label: 'Action', icon: Square }
  ]

  const handleCreateWorkflow = () => {
    const workflow = {
      id: `workflow-${Date.now()}`,
      ...newWorkflow,
      status: 'draft',
      created: new Date().toISOString().split('T')[0],
      lastRun: 'Never',
      nodes: [],
      connections: []
    }
    
    setWorkflows(prev => [...prev, workflow])
    setNewWorkflow({ name: '', description: '' })
    setIsCreateDialogOpen(false)
    setSelectedWorkflow(workflow)
    setCanvasNodes([])
    setCanvasConnections([])
  }

  const handleWorkflowSelect = (workflow) => {
    setSelectedWorkflow(workflow)
    setCanvasNodes(workflow.nodes || [])
    setCanvasConnections(workflow.connections || [])
  }

  const addNodeToCanvas = (nodeType) => {
    const newNode = {
      id: `node-${Date.now()}`,
      type: nodeType,
      name: `New ${nodeType}`,
      x: Math.random() * 400 + 100,
      y: Math.random() * 300 + 100,
      framework: nodeType === 'agent' ? 'AutoGen' : undefined
    }
    
    setCanvasNodes(prev => [...prev, newNode])
  }

  const updateNode = (nodeId, updates) => {
    setCanvasNodes(prev => prev.map(node => 
      node.id === nodeId ? { ...node, ...updates } : node
    ))
  }

  const deleteNode = (nodeId) => {
    setCanvasNodes(prev => prev.filter(node => node.id !== nodeId))
    setCanvasConnections(prev => prev.filter(conn => 
      conn.from !== nodeId && conn.to !== nodeId
    ))
    if (selectedNode?.id === nodeId) {
      setSelectedNode(null)
    }
  }

  const saveWorkflow = () => {
    if (selectedWorkflow) {
      setWorkflows(prev => prev.map(workflow => 
        workflow.id === selectedWorkflow.id 
          ? { ...workflow, nodes: canvasNodes, connections: canvasConnections }
          : workflow
      ))
      alert('Workflow saved successfully!')
    }
  }

  const getStatusBadge = (status) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-yellow-100 text-yellow-800',
      paused: 'bg-gray-100 text-gray-800'
    }
    return variants[status] || variants.draft
  }

  const getNodeIcon = (type) => {
    switch (type) {
      case 'agent':
        return <Circle className="h-4 w-4" />
      case 'condition':
        return <GitBranch className="h-4 w-4" />
      case 'action':
        return <Square className="h-4 w-4" />
      default:
        return <Circle className="h-4 w-4" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Builder</h1>
          <p className="text-gray-600">Design and manage multi-agent workflows</p>
        </div>
        
        <div className="flex space-x-3">
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Workflow
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create New Workflow</DialogTitle>
                <DialogDescription>
                  Design a new multi-agent workflow
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Workflow Name</Label>
                  <Input
                    id="name"
                    value={newWorkflow.name}
                    onChange={(e) => setNewWorkflow(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter workflow name"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={newWorkflow.description}
                    onChange={(e) => setNewWorkflow(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Describe the workflow purpose"
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateWorkflow} disabled={!newWorkflow.name}>
                  Create Workflow
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Workflow List */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Workflows</CardTitle>
              <CardDescription>Select a workflow to edit</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {workflows.map((workflow) => (
                <div
                  key={workflow.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    selectedWorkflow?.id === workflow.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => handleWorkflowSelect(workflow)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-sm">{workflow.name}</h4>
                    <Badge className={getStatusBadge(workflow.status)}>
                      {workflow.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mb-2">{workflow.description}</p>
                  <p className="text-xs text-gray-400">Last run: {workflow.lastRun}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Canvas Area */}
        <div className="lg:col-span-2">
          <Card className="h-[600px]">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>
                    {selectedWorkflow ? selectedWorkflow.name : 'Select a Workflow'}
                  </CardTitle>
                  <CardDescription>
                    {selectedWorkflow ? 'Drag and drop to design your workflow' : 'Choose a workflow from the list to start editing'}
                  </CardDescription>
                </div>
                {selectedWorkflow && (
                  <div className="flex space-x-2">
                    <Button size="sm" variant="outline" onClick={saveWorkflow}>
                      <Save className="h-4 w-4 mr-1" />
                      Save
                    </Button>
                    <Button size="sm">
                      <Play className="h-4 w-4 mr-1" />
                      Run
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="h-full">
              {selectedWorkflow ? (
                <div className="relative w-full h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 overflow-hidden">
                  {/* Canvas Nodes */}
                  {canvasNodes.map((node) => (
                    <div
                      key={node.id}
                      className={`absolute w-32 h-20 bg-white border-2 rounded-lg shadow-sm cursor-pointer transition-all ${
                        selectedNode?.id === node.id ? 'border-blue-500 shadow-md' : 'border-gray-300 hover:border-gray-400'
                      }`}
                      style={{ left: node.x, top: node.y }}
                      onClick={() => setSelectedNode(node)}
                    >
                      <div className="p-2 h-full flex flex-col justify-center items-center text-center">
                        {getNodeIcon(node.type)}
                        <p className="text-xs font-medium mt-1">{node.name}</p>
                        {node.framework && (
                          <p className="text-xs text-gray-500">{node.framework}</p>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {/* Canvas Connections */}
                  <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    {canvasConnections.map((connection, index) => {
                      const fromNode = canvasNodes.find(n => n.id === connection.from)
                      const toNode = canvasNodes.find(n => n.id === connection.to)
                      
                      if (!fromNode || !toNode) return null
                      
                      const x1 = fromNode.x + 64 // center of node
                      const y1 = fromNode.y + 40
                      const x2 = toNode.x + 64
                      const y2 = toNode.y + 40
                      
                      return (
                        <g key={index}>
                          <line
                            x1={x1}
                            y1={y1}
                            x2={x2}
                            y2={y2}
                            stroke="#6B7280"
                            strokeWidth="2"
                            markerEnd="url(#arrowhead)"
                          />
                          <defs>
                            <marker
                              id="arrowhead"
                              markerWidth="10"
                              markerHeight="7"
                              refX="9"
                              refY="3.5"
                              orient="auto"
                            >
                              <polygon
                                points="0 0, 10 3.5, 0 7"
                                fill="#6B7280"
                              />
                            </marker>
                          </defs>
                        </g>
                      )
                    })}
                  </svg>
                  
                  {canvasNodes.length === 0 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <p className="text-gray-500 mb-4">Start building your workflow</p>
                        <p className="text-sm text-gray-400">Add nodes from the panel on the right</p>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-gray-500 mb-4">No workflow selected</p>
                    <p className="text-sm text-gray-400">Choose a workflow from the list to start editing</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Properties Panel */}
        <div className="lg:col-span-1">
          <div className="space-y-4">
            {/* Node Types */}
            <Card>
              <CardHeader>
                <CardTitle>Add Nodes</CardTitle>
                <CardDescription>Drag to add to canvas</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {nodeTypes.map((nodeType) => {
                  const Icon = nodeType.icon
                  return (
                    <Button
                      key={nodeType.type}
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => addNodeToCanvas(nodeType.type)}
                      disabled={!selectedWorkflow}
                    >
                      <Icon className="mr-2 h-4 w-4" />
                      {nodeType.label}
                    </Button>
                  )
                })}
              </CardContent>
            </Card>

            {/* Node Properties */}
            {selectedNode && (
              <Card>
                <CardHeader>
                  <CardTitle>Node Properties</CardTitle>
                  <CardDescription>Configure selected node</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="node-name">Name</Label>
                    <Input
                      id="node-name"
                      value={selectedNode.name}
                      onChange={(e) => updateNode(selectedNode.id, { name: e.target.value })}
                    />
                  </div>
                  
                  {selectedNode.type === 'agent' && (
                    <div>
                      <Label htmlFor="node-framework">Framework</Label>
                      <Select 
                        value={selectedNode.framework} 
                        onValueChange={(value) => updateNode(selectedNode.id, { framework: value })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="AutoGen">AutoGen</SelectItem>
                          <SelectItem value="CrewAI">CrewAI</SelectItem>
                          <SelectItem value="LangGraph">LangGraph</SelectItem>
                          <SelectItem value="MetaGPT">MetaGPT</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                  
                  <Button 
                    variant="destructive" 
                    size="sm" 
                    onClick={() => deleteNode(selectedNode.id)}
                    className="w-full"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Node
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

