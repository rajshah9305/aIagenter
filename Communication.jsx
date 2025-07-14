import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { 
  Send, 
  MessageSquare, 
  Users, 
  Radio,
  Clock,
  CheckCircle,
  AlertCircle,
  Plus,
  Search,
  Filter
} from 'lucide-react'

export default function Communication() {
  const [messages, setMessages] = useState([
    {
      id: 'msg-1',
      from: 'AutoGen Assistant',
      to: 'CrewAI Researcher',
      type: 'request',
      priority: 'normal',
      subject: 'Data Analysis Request',
      content: 'Please analyze the customer feedback data from Q4 2023 and provide insights on sentiment trends.',
      timestamp: '2024-01-15T10:30:00Z',
      status: 'delivered',
      acknowledged: true
    },
    {
      id: 'msg-2',
      from: 'CrewAI Researcher',
      to: 'AutoGen Assistant',
      type: 'response',
      priority: 'normal',
      subject: 'Re: Data Analysis Request',
      content: 'Analysis complete. Found 78% positive sentiment with increasing satisfaction in product quality. Full report attached.',
      timestamp: '2024-01-15T10:45:00Z',
      status: 'delivered',
      acknowledged: true
    },
    {
      id: 'msg-3',
      from: 'LangGraph Processor',
      to: 'MetaGPT Planner',
      type: 'notification',
      priority: 'high',
      subject: 'Workflow Completion',
      content: 'Document processing workflow has completed successfully. 1,247 documents processed with 99.2% accuracy.',
      timestamp: '2024-01-15T11:00:00Z',
      status: 'pending',
      acknowledged: false
    },
    {
      id: 'msg-4',
      from: 'System',
      to: 'All Agents',
      type: 'broadcast',
      priority: 'urgent',
      subject: 'System Maintenance Notice',
      content: 'Scheduled maintenance will begin at 2:00 AM UTC. All agents will be temporarily unavailable for 30 minutes.',
      timestamp: '2024-01-15T11:15:00Z',
      status: 'delivered',
      acknowledged: false
    }
  ])

  const [agents, setAgents] = useState([
    { id: 'agent-1', name: 'AutoGen Assistant', status: 'online', framework: 'AutoGen' },
    { id: 'agent-2', name: 'CrewAI Researcher', status: 'online', framework: 'CrewAI' },
    { id: 'agent-3', name: 'LangGraph Processor', status: 'busy', framework: 'LangGraph' },
    { id: 'agent-4', name: 'MetaGPT Planner', status: 'offline', framework: 'MetaGPT' },
    { id: 'agent-5', name: 'BabyAGI Explorer', status: 'online', framework: 'BabyAGI' }
  ])

  const [topics, setTopics] = useState([
    { id: 'topic-1', name: 'data-analysis', subscribers: 3, description: 'Data analysis and insights' },
    { id: 'topic-2', name: 'workflow-updates', subscribers: 5, description: 'Workflow status updates' },
    { id: 'topic-3', name: 'system-alerts', subscribers: 4, description: 'System alerts and notifications' },
    { id: 'topic-4', name: 'research-results', subscribers: 2, description: 'Research findings and reports' }
  ])

  const [isComposeDialogOpen, setIsComposeDialogOpen] = useState(false)
  const [isBroadcastDialogOpen, setIsBroadcastDialogOpen] = useState(false)
  const [newMessage, setNewMessage] = useState({
    to: '',
    type: 'request',
    priority: 'normal',
    subject: '',
    content: ''
  })
  const [newBroadcast, setNewBroadcast] = useState({
    topic: '',
    priority: 'normal',
    subject: '',
    content: ''
  })

  const [filterType, setFilterType] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  const filteredMessages = messages.filter(message => {
    const matchesType = filterType === 'all' || message.type === filterType
    const matchesStatus = filterStatus === 'all' || message.status === filterStatus
    const matchesSearch = searchTerm === '' || 
      message.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.from.toLowerCase().includes(searchTerm.toLowerCase()) ||
      message.to.toLowerCase().includes(searchTerm.toLowerCase())
    
    return matchesType && matchesStatus && matchesSearch
  })

  const getStatusIcon = (status) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'broadcast':
        return <Radio className="h-4 w-4 text-blue-500" />
      case 'request':
        return <MessageSquare className="h-4 w-4 text-purple-500" />
      case 'response':
        return <MessageSquare className="h-4 w-4 text-green-500" />
      case 'notification':
        return <MessageSquare className="h-4 w-4 text-orange-500" />
      default:
        return <MessageSquare className="h-4 w-4 text-gray-500" />
    }
  }

  const getPriorityBadge = (priority) => {
    const variants = {
      urgent: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      normal: 'bg-blue-100 text-blue-800',
      low: 'bg-gray-100 text-gray-800'
    }
    return variants[priority] || variants.normal
  }

  const getAgentStatusBadge = (status) => {
    const variants = {
      online: 'bg-green-100 text-green-800',
      busy: 'bg-yellow-100 text-yellow-800',
      offline: 'bg-gray-100 text-gray-800'
    }
    return variants[status] || variants.offline
  }

  const handleSendMessage = () => {
    const message = {
      id: `msg-${Date.now()}`,
      from: 'System Admin',
      ...newMessage,
      timestamp: new Date().toISOString(),
      status: 'pending',
      acknowledged: false
    }
    
    setMessages(prev => [message, ...prev])
    setNewMessage({ to: '', type: 'request', priority: 'normal', subject: '', content: '' })
    setIsComposeDialogOpen(false)
  }

  const handleSendBroadcast = () => {
    const broadcast = {
      id: `msg-${Date.now()}`,
      from: 'System Admin',
      to: `Topic: ${newBroadcast.topic}`,
      type: 'broadcast',
      priority: newBroadcast.priority,
      subject: newBroadcast.subject,
      content: newBroadcast.content,
      timestamp: new Date().toISOString(),
      status: 'pending',
      acknowledged: false
    }
    
    setMessages(prev => [broadcast, ...prev])
    setNewBroadcast({ topic: '', priority: 'normal', subject: '', content: '' })
    setIsBroadcastDialogOpen(false)
  }

  const acknowledgeMessage = (messageId) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, acknowledged: true } : msg
    ))
  }

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString()
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Communication</h1>
          <p className="text-gray-600">Inter-agent messaging and communication hub</p>
        </div>
        
        <div className="flex space-x-3">
          <Dialog open={isBroadcastDialogOpen} onOpenChange={setIsBroadcastDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Radio className="mr-2 h-4 w-4" />
                Broadcast
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Send Broadcast Message</DialogTitle>
                <DialogDescription>
                  Send a message to all agents subscribed to a topic
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="broadcast-topic">Topic</Label>
                  <Select value={newBroadcast.topic} onValueChange={(value) => setNewBroadcast(prev => ({ ...prev, topic: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select topic" />
                    </SelectTrigger>
                    <SelectContent>
                      {topics.map(topic => (
                        <SelectItem key={topic.id} value={topic.name}>
                          {topic.name} ({topic.subscribers} subscribers)
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="broadcast-priority">Priority</Label>
                  <Select value={newBroadcast.priority} onValueChange={(value) => setNewBroadcast(prev => ({ ...prev, priority: value }))}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="broadcast-subject">Subject</Label>
                  <Input
                    id="broadcast-subject"
                    value={newBroadcast.subject}
                    onChange={(e) => setNewBroadcast(prev => ({ ...prev, subject: e.target.value }))}
                    placeholder="Enter message subject"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="broadcast-content">Message</Label>
                  <Textarea
                    id="broadcast-content"
                    value={newBroadcast.content}
                    onChange={(e) => setNewBroadcast(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Enter your message"
                    rows={4}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsBroadcastDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSendBroadcast} disabled={!newBroadcast.topic || !newBroadcast.subject || !newBroadcast.content}>
                  <Radio className="mr-2 h-4 w-4" />
                  Send Broadcast
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={isComposeDialogOpen} onOpenChange={setIsComposeDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Compose Message
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Compose Message</DialogTitle>
                <DialogDescription>
                  Send a direct message to an agent
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="message-to">To</Label>
                  <Select value={newMessage.to} onValueChange={(value) => setNewMessage(prev => ({ ...prev, to: value }))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select recipient" />
                    </SelectTrigger>
                    <SelectContent>
                      {agents.map(agent => (
                        <SelectItem key={agent.id} value={agent.name}>
                          {agent.name} ({agent.framework})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label htmlFor="message-type">Type</Label>
                    <Select value={newMessage.type} onValueChange={(value) => setNewMessage(prev => ({ ...prev, type: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="request">Request</SelectItem>
                        <SelectItem value="response">Response</SelectItem>
                        <SelectItem value="notification">Notification</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="message-priority">Priority</Label>
                    <Select value={newMessage.priority} onValueChange={(value) => setNewMessage(prev => ({ ...prev, priority: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="normal">Normal</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="message-subject">Subject</Label>
                  <Input
                    id="message-subject"
                    value={newMessage.subject}
                    onChange={(e) => setNewMessage(prev => ({ ...prev, subject: e.target.value }))}
                    placeholder="Enter message subject"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="message-content">Message</Label>
                  <Textarea
                    id="message-content"
                    value={newMessage.content}
                    onChange={(e) => setNewMessage(prev => ({ ...prev, content: e.target.value }))}
                    placeholder="Enter your message"
                    rows={4}
                  />
                </div>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setIsComposeDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleSendMessage} disabled={!newMessage.to || !newMessage.subject || !newMessage.content}>
                  <Send className="mr-2 h-4 w-4" />
                  Send Message
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          {/* Online Agents */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Users className="mr-2 h-5 w-5" />
                Agents
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {agents.map((agent) => (
                <div key={agent.id} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'online' ? 'bg-green-500' : 
                      agent.status === 'busy' ? 'bg-yellow-500' : 'bg-gray-400'
                    }`} />
                    <div>
                      <p className="text-sm font-medium">{agent.name}</p>
                      <p className="text-xs text-gray-500">{agent.framework}</p>
                    </div>
                  </div>
                  <Badge className={getAgentStatusBadge(agent.status)}>
                    {agent.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Topics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Radio className="mr-2 h-5 w-5" />
                Topics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {topics.map((topic) => (
                <div key={topic.id} className="p-2 border rounded">
                  <div className="flex items-center justify-between mb-1">
                    <p className="text-sm font-medium">{topic.name}</p>
                    <span className="text-xs text-gray-500">{topic.subscribers}</span>
                  </div>
                  <p className="text-xs text-gray-500">{topic.description}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Messages */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Messages</CardTitle>
                  <CardDescription>Inter-agent communication history</CardDescription>
                </div>
                <div className="flex space-x-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                    <Input
                      placeholder="Search messages..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 w-64"
                    />
                  </div>
                  <Select value={filterType} onValueChange={setFilterType}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="Type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      <SelectItem value="request">Request</SelectItem>
                      <SelectItem value="response">Response</SelectItem>
                      <SelectItem value="notification">Notification</SelectItem>
                      <SelectItem value="broadcast">Broadcast</SelectItem>
                    </SelectContent>
                  </Select>
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-[120px]">
                      <SelectValue placeholder="Status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="delivered">Delivered</SelectItem>
                      <SelectItem value="failed">Failed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredMessages.map((message) => (
                  <div key={message.id} className="p-4 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        {getTypeIcon(message.type)}
                        <div>
                          <h4 className="font-medium">{message.subject}</h4>
                          <p className="text-sm text-gray-600">
                            From: <span className="font-medium">{message.from}</span> → 
                            To: <span className="font-medium">{message.to}</span>
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getPriorityBadge(message.priority)}>
                          {message.priority}
                        </Badge>
                        {getStatusIcon(message.status)}
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-700 mb-3">{message.content}</p>
                    
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-gray-500">{formatTimestamp(message.timestamp)}</p>
                      
                      {!message.acknowledged && message.status === 'delivered' && (
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => acknowledgeMessage(message.id)}
                        >
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Acknowledge
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                
                {filteredMessages.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">No messages found matching your criteria.</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

