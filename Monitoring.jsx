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
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Activity,
  Bell,
  Settings,
  Plus,
  Filter,
  RefreshCw
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'

export default function Monitoring() {
  const [alerts, setAlerts] = useState([
    {
      id: 'alert-1',
      type: 'error',
      severity: 'high',
      title: 'Agent Connection Failed',
      message: 'MetaGPT Planner has lost connection and is not responding',
      agent: 'MetaGPT Planner',
      timestamp: '2024-01-15T10:30:00Z',
      status: 'active',
      acknowledged: false
    },
    {
      id: 'alert-2',
      type: 'warning',
      severity: 'medium',
      title: 'High Response Time',
      message: 'AutoGen Assistant response time is above 5 seconds threshold',
      agent: 'AutoGen Assistant',
      timestamp: '2024-01-15T10:25:00Z',
      status: 'active',
      acknowledged: false
    },
    {
      id: 'alert-3',
      type: 'info',
      severity: 'low',
      title: 'Agent Started',
      message: 'CrewAI Researcher has been successfully started',
      agent: 'CrewAI Researcher',
      timestamp: '2024-01-15T10:20:00Z',
      status: 'resolved',
      acknowledged: true
    }
  ])

  const [metrics, setMetrics] = useState([
    { time: '10:00', responseTime: 1.2, throughput: 45, errorRate: 2.1 },
    { time: '10:05', responseTime: 1.5, throughput: 52, errorRate: 1.8 },
    { time: '10:10', responseTime: 2.1, throughput: 48, errorRate: 3.2 },
    { time: '10:15', responseTime: 1.8, throughput: 55, errorRate: 2.5 },
    { time: '10:20', responseTime: 1.3, throughput: 62, errorRate: 1.9 },
    { time: '10:25', responseTime: 3.2, throughput: 38, errorRate: 4.1 },
    { time: '10:30', responseTime: 2.8, throughput: 41, errorRate: 3.8 }
  ])

  const [agentMetrics, setAgentMetrics] = useState([
    {
      id: 'agent-1',
      name: 'AutoGen Assistant',
      status: 'active',
      responseTime: 3.2,
      throughput: 15,
      errorRate: 2.1,
      cpuUsage: 45,
      memoryUsage: 67,
      trend: 'up'
    },
    {
      id: 'agent-2',
      name: 'CrewAI Researcher',
      status: 'active',
      responseTime: 1.8,
      throughput: 22,
      errorRate: 1.2,
      cpuUsage: 32,
      memoryUsage: 54,
      trend: 'stable'
    },
    {
      id: 'agent-3',
      name: 'LangGraph Processor',
      status: 'paused',
      responseTime: 0,
      throughput: 0,
      errorRate: 0,
      cpuUsage: 0,
      memoryUsage: 12,
      trend: 'down'
    }
  ])

  const [isCreateRuleDialogOpen, setIsCreateRuleDialogOpen] = useState(false)
  const [newRule, setNewRule] = useState({
    name: '',
    metric: '',
    operator: '>',
    threshold: '',
    severity: 'medium'
  })

  const [filterSeverity, setFilterSeverity] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')

  const filteredAlerts = alerts.filter(alert => {
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity
    const matchesStatus = filterStatus === 'all' || alert.status === filterStatus
    return matchesSeverity && matchesStatus
  })

  const getAlertIcon = (type) => {
    switch (type) {
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case 'info':
        return <CheckCircle className="h-5 w-5 text-blue-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getSeverityBadge = (severity) => {
    const variants = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800'
    }
    return variants[severity] || variants.low
  }

  const getStatusBadge = (status) => {
    const variants = {
      active: 'bg-red-100 text-red-800',
      resolved: 'bg-green-100 text-green-800',
      acknowledged: 'bg-yellow-100 text-yellow-800'
    }
    return variants[status] || variants.active
  }

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4 text-red-500" />
      case 'down':
        return <TrendingDown className="h-4 w-4 text-green-500" />
      default:
        return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const acknowledgeAlert = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, acknowledged: true, status: 'acknowledged' }
        : alert
    ))
  }

  const resolveAlert = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId 
        ? { ...alert, status: 'resolved' }
        : alert
    ))
  }

  const handleCreateRule = () => {
    // In a real implementation, this would create an alert rule
    console.log('Creating alert rule:', newRule)
    setNewRule({ name: '', metric: '', operator: '>', threshold: '', severity: 'medium' })
    setIsCreateRuleDialogOpen(false)
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Monitoring</h1>
          <p className="text-gray-600">Real-time monitoring and alerting for your agents</p>
        </div>
        
        <div className="flex space-x-3">
          <Button variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Dialog open={isCreateRuleDialogOpen} onOpenChange={setIsCreateRuleDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Create Alert Rule
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Create Alert Rule</DialogTitle>
                <DialogDescription>
                  Set up a new monitoring rule for your agents
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="rule-name">Rule Name</Label>
                  <Input
                    id="rule-name"
                    value={newRule.name}
                    onChange={(e) => setNewRule(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="High response time alert"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="metric">Metric</Label>
                  <Select value={newRule.metric} onValueChange={(value) => setNewRule(prev => ({ ...prev, metric: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select metric" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="response_time">Response Time</SelectItem>
                      <SelectItem value="error_rate">Error Rate</SelectItem>
                      <SelectItem value="cpu_usage">CPU Usage</SelectItem>
                      <SelectItem value="memory_usage">Memory Usage</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="operator">Operator</Label>
                    <Select value={newRule.operator} onValueChange={(value) => setNewRule(prev => ({ ...prev, operator: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=">">Greater than</SelectItem>
                        <SelectItem value="<">Less than</SelectItem>
                        <SelectItem value="==">Equal to</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="threshold">Threshold</Label>
                    <Input
                      id="threshold"
                      value={newRule.threshold}
                      onChange={(e) => setNewRule(prev => ({ ...prev, threshold: e.target.value }))}
                      placeholder="5.0"
                    />
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="severity">Severity</Label>
                  <Select value={newRule.severity} onValueChange={(value) => setNewRule(prev => ({ ...prev, severity: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsCreateRuleDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleCreateRule} disabled={!newRule.name || !newRule.metric || !newRule.threshold}>
                  Create Rule
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Metrics Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Metrics Chart */}
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
            <CardDescription>Real-time performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="responseTime" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} />
                <Area type="monotone" dataKey="errorRate" stackId="2" stroke="#EF4444" fill="#EF4444" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Agent Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Performance</CardTitle>
            <CardDescription>Individual agent metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {agentMetrics.map((agent) => (
                <div key={agent.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${
                        agent.status === 'active' ? 'bg-green-500' : 
                        agent.status === 'paused' ? 'bg-yellow-500' : 'bg-red-500'
                      }`} />
                      <h4 className="font-medium">{agent.name}</h4>
                    </div>
                    {getTrendIcon(agent.trend)}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Response Time</p>
                      <p className="font-medium">{agent.responseTime}s</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Throughput</p>
                      <p className="font-medium">{agent.throughput}/min</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Error Rate</p>
                      <p className="font-medium">{agent.errorRate}%</p>
                    </div>
                    <div>
                      <p className="text-gray-500">CPU Usage</p>
                      <p className="font-medium">{agent.cpuUsage}%</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Alerts</CardTitle>
              <CardDescription>System alerts and notifications</CardDescription>
            </div>
            <div className="flex space-x-2">
              <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severity</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="acknowledged">Acknowledged</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredAlerts.map((alert) => (
              <div key={alert.id} className="flex items-start space-x-4 p-4 border rounded-lg">
                {getAlertIcon(alert.type)}
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium">{alert.title}</h4>
                    <div className="flex space-x-2">
                      <Badge className={getSeverityBadge(alert.severity)}>
                        {alert.severity}
                      </Badge>
                      <Badge className={getStatusBadge(alert.status)}>
                        {alert.status}
                      </Badge>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-2">{alert.message}</p>
                  
                  <div className="flex items-center justify-between">
                    <div className="text-xs text-gray-500">
                      <span className="font-medium">{alert.agent}</span> • {formatTimestamp(alert.timestamp)}
                    </div>
                    
                    {alert.status === 'active' && (
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => acknowledgeAlert(alert.id)}
                        >
                          <Bell className="h-3 w-3 mr-1" />
                          Acknowledge
                        </Button>
                        <Button 
                          size="sm"
                          onClick={() => resolveAlert(alert.id)}
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Resolve
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {filteredAlerts.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No alerts found matching your criteria.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

