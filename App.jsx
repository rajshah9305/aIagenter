import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Activity, Users, Workflow, MessageSquare, Settings, BarChart3 } from 'lucide-react'
import Dashboard from './components/Dashboard'
import AgentManagement from './components/AgentManagement'
import WorkflowBuilder from './components/WorkflowBuilder'
import Monitoring from './components/Monitoring'
import Communication from './components/Communication'
import Sidebar from './components/Sidebar'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: BarChart3 },
    { id: 'agents', name: 'Agents', icon: Users },
    { id: 'workflows', name: 'Workflows', icon: Workflow },
    { id: 'monitoring', name: 'Monitoring', icon: Activity },
    { id: 'communication', name: 'Communication', icon: MessageSquare },
    { id: 'settings', name: 'Settings', icon: Settings },
  ]

  return (
    <Router>
      <div className="flex h-screen bg-gray-50">
        <Sidebar 
          navigation={navigation} 
          activeTab={activeTab} 
          setActiveTab={setActiveTab} 
        />
        
        <main className="flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto">
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'agents' && <AgentManagement />}
            {activeTab === 'workflows' && <WorkflowBuilder />}
            {activeTab === 'monitoring' && <Monitoring />}
            {activeTab === 'communication' && <Communication />}
            {activeTab === 'settings' && <div className="p-6"><h1 className="text-2xl font-bold">Settings</h1></div>}
          </div>
        </main>
      </div>
    </Router>
  )
}

export default App
