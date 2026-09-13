import React, { useState } from 'react';
import api from '../services/api';
import { useNavigate, Link } from 'react-router-dom';
import { UserPlus, Building2 } from 'lucide-react';

export const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/auth/register/', { username, email, password });
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] p-4 font-sans">
      <div className="app-card w-full max-w-md p-8 border-[#3b4b68] shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded bg-[#00a09d]/20 border border-[#00a09d]/40 mx-auto mb-3 flex items-center justify-center text-[#00a09d]">
            <Building2 size={26} />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Create Admin Account</h2>
          <p className="text-xs text-[#94a3b8] mt-1">Register to launch your multi-tenant e-commerce shop</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1.5">Username</label>
            <input
              type="text"
              className="app-input"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              placeholder="Choose admin username..."
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1.5">Email Address</label>
            <input
              type="email"
              className="app-input"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="admin@example.com"
            />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-300 uppercase tracking-wider block mb-1.5">Password</label>
            <input
              type="password"
              className="app-input"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="Choose secure password..."
            />
          </div>
          <button
            type="submit"
            className="mt-2 w-full app-btn-teal py-2.5 text-xs font-bold flex items-center justify-center gap-2"
          >
            <UserPlus size={14} /> Register Admin Account
          </button>
        </form>

        <div className="text-center mt-6 text-xs text-[#94a3b8]">
          Already have an account? <Link to="/login" className="text-[#7c7bad] font-bold hover:underline">Log In</Link>
        </div>
      </div>
    </div>
  );
};

