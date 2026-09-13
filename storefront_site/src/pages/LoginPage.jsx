import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link, useLocation } from 'react-router-dom';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();

  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(username, password);
      const searchParams = new URLSearchParams(location.search);
      const redirectParam = searchParams.get('redirect');
      const savedRedirect = localStorage.getItem('redirect_after_login');
      const stateFrom = location.state?.from;

      const target = redirectParam || savedRedirect || stateFrom || '/';
      localStorage.removeItem('redirect_after_login');
      navigate(target, { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center pt-8 pb-16 px-4">
      {/* Store Logo placeholder */}
      <Link to="/" className="mb-6 font-extrabold text-2xl tracking-tight text-amazon-dark-navy">
        Amazon<span className="text-amazon-orange">Clone</span>
      </Link>

      <div className="w-full max-w-[350px]">
        <div className="border border-[#D5D9D9] rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-normal text-[#111] mb-4">Sign in</h1>

          {error && (
            <div className="mb-4 text-[#c40000] text-sm flex items-start gap-2">
              <span className="font-bold">!</span>
              <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="text-sm font-bold text-[#111] block mb-1">Username</label>
              <input
                type="text"
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="text-sm font-bold text-[#111] block mb-1">Password</label>
              <input
                type="password"
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" disabled={submitting} className="btn-buy-now w-full py-2 shadow-sm rounded-lg mt-2 text-sm disabled:opacity-50">
              {submitting ? 'Signing in...' : 'Continue'}
            </button>

            <div className="text-xs text-[#111] mt-3">
              By continuing, you agree to AmazonClone's <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">Conditions of Use</span> and <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">Privacy Notice</span>.
            </div>
            
            <div className="mt-4 pt-4 border-t border-[#D5D9D9]">
              <span className="text-sm text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline flex items-center gap-1 group">
                <span className="text-amazon-text-secondary group-hover:text-amazon-orange transition-colors">►</span> Need help?
              </span>
            </div>
          </form>
        </div>

        <div className="relative text-center mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-[#D5D9D9]"></div>
          </div>
          <span className="relative bg-white px-2 text-xs text-[#767676]">
            New to AmazonClone?
          </span>
        </div>

        <Link to="/register" className="block text-center w-full bg-white border border-[#D5D9D9] shadow-sm rounded-lg py-1.5 text-sm font-normal text-[#111] hover:bg-[#F0F2F2] transition-colors">
          Create your AmazonClone account
        </Link>
      </div>

      {/* Footer minimal */}
      <div className="mt-12 w-full max-w-xl mx-auto pt-8 border-t border-[#D5D9D9] flex justify-center gap-8 text-xs text-amazon-link-teal">
        <span className="cursor-pointer hover:text-amazon-orange hover:underline">Conditions of Use</span>
        <span className="cursor-pointer hover:text-amazon-orange hover:underline">Privacy Notice</span>
        <span className="cursor-pointer hover:text-amazon-orange hover:underline">Help</span>
      </div>
      <div className="mt-2 text-xs text-amazon-text-secondary">
        © 2024-2025, AmazonClone.com, Inc. or its affiliates
      </div>
    </div>
  );
};
