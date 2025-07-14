import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { 
  Activity, 
  Users, 
  MessageSquare, 
  AlertTriangle, 
  TrendingUp, 
  Clock,
  CheckCircle,
  XCircle,
  Pause
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState({
    overview: {
      totalAgents: 12,
      activeAgents: 8,
      totalTasks: 156,
      activeTasks: 23,
      totalMessages: 1247,
      activeAlerts: 3
    },
    agents: [
      { id: 'agent-1', name: 'AutoGen Assistant', framework: 'AutoGen', status: 'active', tasks: 15, uptime: '2h 34m' },
      { id: 'agent-2', name: 'CrewAI Researcher', framework: 'CrewAI', status: 'active', tasks: 8, uptime: '1h 12m' },
      { id: 'agent-3', name: 'LangGraph Processor', framework: 'LangGraph', status: 'paused', tasks: 0, uptime: '0m' },
      { id: 'agent-4', name: 'MetaGPT Planner', framework: 'MetaGPT', status: 'error', tasks: 0, uptime: '0m' },
    ],
    metrics: [
      { time: '00:00', tasks: 45, messages: 120, agents: 8 },
      { time: '04:00', tasks: 52, messages: 145, agents: 9 },
      { time: '08:00', tasks: 68, messages: 180, agents: 10 },
      { time: '12:00', tasks: 75, messages: 210, agents: 12 },
      { time: '16:00', tasks: 82, messages: 195, agents: 11 },
      { time: '20:00', tasks: 78, messages: 165, agents: 10 },
    ],
    frameworkDistribution: [
      { name: 'AutoGen', value: 35, color: '#3B82F6' },
      { name: 'CrewAI', value: 25, color: '#10B981' },
      { name: 'LangGraph', value: 20, color: '#F59E0B' },
      { name: 'MetaGPT', value: 15, color: '#EF4444' },
      { name: 'Others', value: 5, color: '#8B5CF6' },
    ],
    recentAlerts: [
      { id: 1, type: 'warning', message: 'Agent response time above threshold', time: '2 min ago' },
      { id: 2, type: 'error', message: 'MetaGPT Planner connection failed', time: '5 min ago' },
      { id: 3, type: 'info', message: 'New agent registered successfully', time: '10 min ago' },
    ]
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

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor and manage your AI agent ecosystem</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline">
            <Activity className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button>
            <Users className="mr-2 h-4 w-4" />
            Add Agent
          </Button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.overview.totalAgents}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+2</span> from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Tasks</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.overview.activeTasks}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-blue-600">+5</span> from last hour
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Messages</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.overview.totalMessages}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">+12%</span> from yesterday
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{dashboardData.overview.activeAlerts}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-red-600">+1</span> new alert
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Metrics Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Metrics</CardTitle>
            <CardDescription>Tasks and messages over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dashboardData.metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="tasks" stroke="#3B82F6" strokeWidth={2} />
                <Line type="monotone" dataKey="messages" stroke="#10B981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Framework Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Framework Distribution</CardTitle>
            <CardDescription>Agent distribution by framework</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dashboardData.frameworkDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}%`}
                >
                  {dashboardData.frameworkDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Agents */}
        <Card>
          <CardHeader>
            <CardTitle>Active Agents</CardTitle>
            <CardDescription>Current status of your AI agents</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.agents.map((agent) => (
                <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(agent.status)}
                    <div>
                      <p className="font-medium">{agent.name}</p>
                      <p className="text-sm text-gray-500">{agent.framework}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className={getStatusBadge(agent.status)}>
                      {agent.status}
                    </Badge>
                    <div className="text-right">
                      <p className="text-sm font-medium">{agent.tasks} tasks</p>
                      <p className="text-xs text-gray-500">{agent.uptime}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
            <CardDescription>Latest system notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData.recentAlerts.map((alert) => (
                <div key={alert.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    alert.type === 'error' ? 'bg-red-500' :
                    alert.type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{alert.message}</p>
                    <p className="text-xs text-gray-500">{alert.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

