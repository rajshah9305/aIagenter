import React from "react";

export default function Settings({ darkMode, setDarkMode }) {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">Settings</h1>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">Appearance</h2>
        <button
          className="px-4 py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 transition-colors"
          onClick={() => setDarkMode((d) => !d)}
        >
          Toggle {darkMode ? "Light" : "Dark"} Mode
        </button>
      </div>
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">User Profile & API Keys</h2>
        <div className="text-gray-600 dark:text-gray-300">(Coming soon: Manage your profile and API keys here.)</div>
      </div>
    </div>
  );
} 