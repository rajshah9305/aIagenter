import React from "react";
import { NavLink } from "react-router-dom";
import { Home, Users, Workflow, Activity, MessageSquare, Settings, Moon, Sun } from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard", icon: <Home /> },
  { to: "/agents", label: "Agents", icon: <Users /> },
  { to: "/workflows", label: "Workflows", icon: <Workflow /> },
  { to: "/monitoring", label: "Monitoring", icon: <Activity /> },
  { to: "/communication", label: "Communication", icon: <MessageSquare /> },
  { to: "/settings", label: "Settings", icon: <Settings /> },
];

export default function Sidebar({ darkMode, setDarkMode }) {
  return (
    <aside className="fixed left-0 top-0 h-full w-20 bg-white dark:bg-gray-800 shadow-lg flex flex-col items-center py-6 z-20">
      <div className="mb-8">
        <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">AO</span>
      </div>
      <nav className="flex flex-col gap-6 flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex flex-col items-center text-gray-500 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors ${
                isActive ? "text-blue-600 dark:text-blue-400" : ""
              }`
            }
            end
          >
            {item.icon}
            <span className="text-xs mt-1">{item.label}</span>
          </NavLink>
        ))}
      </nav>
      <button
        className="mt-8 p-2 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-blue-100 dark:hover:bg-blue-900 transition-colors"
        onClick={() => setDarkMode((d) => !d)}
        aria-label="Toggle dark mode"
      >
        {darkMode ? <Sun /> : <Moon />}
      </button>
    </aside>
  );
} 