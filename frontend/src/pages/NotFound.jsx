import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <h1 className="text-6xl font-bold text-blue-600 dark:text-blue-400 mb-4">404</h1>
      <p className="text-xl text-gray-700 dark:text-gray-300 mb-8">Page Not Found</p>
      <Link to="/" className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">Go to Dashboard</Link>
    </div>
  );
} 