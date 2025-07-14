import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { 
  Plus, 
  Search, 
  Filter, 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  MoreHorizontal
} from 'lucide-react'

export default function AgentManagement() {
  const [agents, setAgents] = useState([
    {
      id: 'agent-1',
      name: 'AutoGen Assistant',
      framework: 'AutoGen',
      status: 'active',
      version: '0.2.0',
      description: 'Multi-agent conversation system for complex tasks',
      created: '2024-01-15',
      lastActive: '2 minutes ago',
      tasks: 15,
      successRate: 94,
      avgResponseTime: 1.2
    },
    {
      id: 'agent-2',
      name: 'CrewAI Researcher',
      framework: 'CrewAI',
      status: 'active',
      version: '0.1.0',
      description: 'Research and analysis crew for data gathering',
      created: '2024-01-12',
      lastActive: '5 minutes ago',
      tasks: 8,
      successRate: 98,
      avgResponseTime: 2.1
    },
    {
      id: 'agent-3',
      name: 'LangGraph Processor',
      framework: 'LangGraph',
      status: 'paused',
      version: '0.3.1',
      description: 'Graph-based workflow processing agent',
      created: '2024-01-10',
      lastActive: '1 hour ago',
      tasks: 0,
      successRate: 89,
      avgResponseTime: 0.8
    },
    {
      id: 'agent-4',
      name: 'MetaGPT Planner',
      framework: 'MetaGPT',
      status: 'error',
      version: '0.4.0',
      description: 'Strategic planning and project management',
      created: '2024-01-08',
      lastActive: '3 hours ago',
      tasks: 0,
      successRate: 76,
      avgResponseTime: 3.5
    },
    {
      id: 'agent-5',
      name: 'BabyAGI Explorer',
      framework: 'BabyAGI',
      status: 'inactive',
      version: '1.0.0',
      description: 'Autonomous task exploration and execution',
      created: '2024-01-05',
      lastActive: '1 day ago',
      tasks: 0,
      successRate: 82,
      avgResponseTime: 2.8
    }
  ])

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [frameworkFilter, setFrameworkFilter] = useState('all')
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [newAgent, setNewAgent] = useState({
    name: '',
    framework: '',
    description: '',
    version: '1.0.0'
  })

  const frameworks = ['AutoGen', 'CrewAI', 'LangGraph', 'MetaGPT', 'BabyAGI', 'MiniAGI']

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.framework.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || agent.status === statusFilter
    const matchesFramework = frameworkFilter === 'all' || agent.framework === frameworkFilter
    
    return matchesSearch && matchesStatus && matchesFramework
  })

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'paused':
        return <Pause className="h-4 w-4 text-yellow-500" />
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status) => {
    const variants = {
      active: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      error: 'bg-red-100 text-red-800',
      inactive: 'bg-gray-100 text-gray-800'
    }
    return variants[status] || variants.inactive
  }

  const handleAgentAction = (agentId, action) => {
    setAgents(prev => prev.map(agent => {
      if (agent.id === agentId) {
        switch (action) {
          case 'start':
            return { ...agent, status: 'active', lastActive: 'Just now' }
          case 'pause':
            return { ...agent, status: 'paused' }
          case 'stop':
            return { ...agent, status: 'inactive' }
          default:
            return agent
        }
      }
      return agent
    }))
  }

  const handleCreateAgent = () => {
    const agent = {
      id: `agent-${Date.now()}`,
      ...newAgent,
      status: 'inactive',
      created: new Date().toISOString().split('T')[0],
      lastActive: 'Never',
      tasks: 0,
      successRate: 0,
      avgResponseTime: 0
    }
    
    setAgents(prev => [...prev, agent])
    setNewAgent({ name: '', framework: '', description: '', version: '1.0.0' })
    setIsCreateDialogOpen(false)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Agent Management</h1>
          <p className="text-gray-600">Manage and monitor your AI agents</p>
        </div>
        
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Agent
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create New Agent</DialogTitle>
              <DialogDescription>
                Configure a new AI agent for your orchestra
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid gap-2">
                <Label htmlFor="name">Agent Name</Label>
                <Input
                  id="name"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter agent name"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="framework">Framework</Label>
                <Select value={newAgent.framework} onValueChange={(value) => setNewAgent(prev => ({ ...prev, framework: value }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select framework" />
                  </SelectTrigger>
                  <SelectContent>
                    {frameworks.map(framework => (
                      <SelectItem key={framework} value={framework}>{framework}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="version">Version</Label>
                <Input
                  id="version"
                  value={newAgent.version}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, version: e.target.value }))}
                  placeholder="1.0.0"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={newAgent.description}
                  onChange={(e) => setNewAgent(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe the agent's purpose and capabilities"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateAgent} disabled={!newAgent.name || !newAgent.framework}>
                Create Agent
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search agents..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
            <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by framework" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Frameworks</SelectItem>
                {frameworks.map(framework => (
                  <SelectItem key={framework} value={framework}>{framework}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map((agent) => (
          <Card key={agent.id} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(agent.status)}
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <CardDescription>{agent.framework} v{agent.version}</CardDescription>
                  </div>
                </div>
                <Badge className={getStatusBadge(agent.status)}>
                  {agent.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-gray-600">{agent.description}</p>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Tasks</p>
                  <p className="font-medium">{agent.tasks}</p>
                </div>
                <div>
                  <p className="text-gray-500">Success Rate</p>
                  <p className="font-medium">{agent.successRate}%</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg Response</p>
                  <p className="font-medium">{agent.avgResponseTime}s</p>
                </div>
                <div>
                  <p className="text-gray-500">Last Active</p>
                  <p className="font-medium">{agent.lastActive}</p>
                </div>
              </div>

              <div className="flex space-x-2 pt-2">
                {agent.status === 'active' ? (
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleAgentAction(agent.id, 'pause')}
                  >
                    <Pause className="h-3 w-3 mr-1" />
                    Pause
                  </Button>
                ) : (
                  <Button 
                    size="sm"
                    onClick={() => handleAgentAction(agent.id, 'start')}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    Start
                  </Button>
                )}
                
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleAgentAction(agent.id, 'stop')}
                >
                  <Square className="h-3 w-3 mr-1" />
                  Stop
                </Button>
                
                <Button size="sm" variant="outline">
                  <Settings className="h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-gray-500">No agents found matching your criteria.</p>
            <Button className="mt-4" onClick={() => setIsCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Your First Agent
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

