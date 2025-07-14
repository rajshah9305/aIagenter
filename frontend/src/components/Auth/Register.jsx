import React, { useState } from "react";
// import { useNavigate } from "react-router-dom";
// import { register } from "../../utils/api";

export default function Register() {
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  // const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    // try {
    //   await register(form);
    //   navigate("/login");
    // } catch (err) {
    //   setError("Registration failed");
    // }
    setError("Demo: Registration not connected");
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <form className="bg-white dark:bg-gray-800 p-8 rounded shadow-md w-full max-w-md" onSubmit={handleSubmit}>
        <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Register</h2>
        {error && <div className="mb-4 text-red-500">{error}</div>}
        <input
          className="w-full mb-4 px-4 py-2 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
          type="text"
          placeholder="Username"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <input
          className="w-full mb-4 px-4 py-2 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <input
          className="w-full mb-6 px-4 py-2 rounded border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-white"
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
        />
        <button className="w-full py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition-colors" type="submit">
          Register
        </button>
        <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
          Already have an account? <a href="/login" className="text-blue-600 dark:text-blue-400">Login</a>
        </div>
      </form>
    </div>
  );
} 