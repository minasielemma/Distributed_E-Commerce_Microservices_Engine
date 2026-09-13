import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { LogIn, Building2 } from 'lucide-react';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      navigate('/tenants');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] p-4 font-sans">
      <div className="app-card w-full max-w-md p-8 border-[#3b4b68] shadow-2xl">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded bg-[#7c7bad]/20 border border-[#7c7bad]/40 mx-auto mb-3 flex items-center justify-center text-[#7c7bad]">
            <Building2 size={26} />
          </div>
          <h2 className="text-xl font-bold text-white tracking-tight">Enterprise Admin Portal</h2>
          <p className="text-xs text-[#94a3b8] mt-1">Multi-Tenant SaaS Control Panel & Management</p>
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
              placeholder="Enter admin username..."
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
              placeholder="Enter account password..."
            />
          </div>
          <button
            type="submit"
            className="mt-2 w-full app-btn-primary py-2.5 text-xs font-bold flex items-center justify-center gap-2"
          >
            <LogIn size={14} /> Sign In to ERP Control Panel
          </button>
        </form>

        <div className="text-center mt-6 text-xs text-[#94a3b8]">
          Don't have an account? <Link to="/register" className="text-[#00a09d] font-bold hover:underline">Register Shop Tenant</Link>
        </div>
      </div>
    </div>
  );
};

