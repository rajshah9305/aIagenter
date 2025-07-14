import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./components/Dashboard";
import AgentManagement from "./components/AgentManagement";
import WorkflowBuilder from "./components/WorkflowBuilder";
import Monitoring from "./components/Monitoring";
import Communication from "./components/Communication";
import Settings from "./components/Settings";
import Login from "./components/Auth/Login";
import Register from "./components/Auth/Register";
import NotFound from "./pages/NotFound";
// import { useAuth } from "./hooks/useAuth";

function App() {
  const [darkMode, setDarkMode] = useState(false);
  // const { isAuthenticated } = useAuth();
  const isAuthenticated = true; // For demo, set to true

  return (
    <div className={darkMode ? "dark" : ""}>
      <Router>
        {isAuthenticated && <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} />}
        <main className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            {isAuthenticated ? (
              <>
                <Route path="/" element={<Dashboard />} />
                <Route path="/agents" element={<AgentManagement />} />
                <Route path="/workflows" element={<WorkflowBuilder />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/communication" element={<Communication />} />
                <Route path="/settings" element={<Settings darkMode={darkMode} setDarkMode={setDarkMode} />} />
                <Route path="*" element={<NotFound />} />
              </>
            ) : (
              <Route path="*" element={<Navigate to="/login" />} />
            )}
          </Routes>
        </main>
      </Router>
    </div>
  );
}

export default App; 