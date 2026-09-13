import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

export const RegisterPage = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  const { register, login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords must match');
      return;
    }

    if (password.length < 6) {
      setError('Passwords must be at least 6 characters.');
      return;
    }

    setSubmitting(true);
    try {
      await register(username, email, password);
      setSuccess(true);
      // Auto login after registration
      setTimeout(async () => {
        try {
          await login(username, password);
          const savedRedirect = localStorage.getItem('redirect_after_login');
          const target = savedRedirect || '/';
          localStorage.removeItem('redirect_after_login');
          navigate(target, { replace: true });
        } catch {
          navigate('/login');
        }
      }, 1000);
    } catch (err) {
      const responseErrors = err.response?.data;
      if (typeof responseErrors === 'object') {
        const firstErrorKey = Object.keys(responseErrors)[0];
        const errorVal = responseErrors[firstErrorKey];
        setError(Array.isArray(errorVal) ? errorVal[0] : String(errorVal));
      } else {
        setError('Failed to create account. Please check your details.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center pt-8 pb-16 px-4">
      {/* Store Logo */}
      <Link to="/" className="mb-6 font-extrabold text-2xl tracking-tight text-amazon-dark-navy">
        Amazon<span className="text-amazon-orange">Clone</span>
      </Link>

      <div className="w-full max-w-[350px]">
        <div className="border border-[#D5D9D9] rounded-lg p-6 mb-6">
          <h1 className="text-3xl font-normal text-[#111] mb-4">Create account</h1>

          {error && (
            <div className="mb-4 text-[#c40000] text-sm flex items-start gap-2">
              <span className="font-bold">!</span>
              <span>{typeof error === 'string' ? error : JSON.stringify(error)}</span>
            </div>
          )}

          {success ? (
            <div className="text-center py-6">
              <div className="text-amazon-stock-green font-bold text-lg mb-2">Account created successfully!</div>
              <p className="text-sm text-[#111]">Signing you in...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex flex-col gap-3">
              <div>
                <label className="text-sm font-bold text-[#111] block mb-1">Your name (Username)</label>
                <input
                  type="text"
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  placeholder="First and last name"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-sm font-bold text-[#111] block mb-1">Email</label>
                <input
                  type="email"
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="text-sm font-bold text-[#111] block mb-1">Password</label>
                <input
                  type="password"
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  placeholder="At least 6 characters"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                />
                <div className="text-xs text-[#111] flex items-center gap-1 mt-1">
                  <span className="text-blue-600 font-bold italic">i</span> Passwords must be at least 6 characters.
                </div>
              </div>

              <div>
                <label className="text-sm font-bold text-[#111] block mb-1">Re-enter password</label>
                <input
                  type="password"
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                />
              </div>

              <button 
                type="submit" 
                disabled={submitting} 
                className="btn-buy-now w-full py-2 shadow-sm rounded-lg mt-2 text-sm disabled:opacity-50"
              >
                {submitting ? 'Creating account...' : 'Continue'}
              </button>

              <div className="text-xs text-[#111] mt-3">
                By creating an account, you agree to AmazonClone's <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">Conditions of Use</span> and <span className="text-amazon-link-teal cursor-pointer hover:text-amazon-orange hover:underline">Privacy Notice</span>.
              </div>

              <div className="mt-4 pt-4 border-t border-[#D5D9D9] text-sm text-[#111]">
                Already have an account? <Link to="/login" className="text-amazon-link-teal hover:text-amazon-orange hover:underline">Sign in <span className="text-xs">►</span></Link>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Footer minimal */}
      <div className="mt-8 w-full max-w-xl mx-auto pt-8 border-t border-[#D5D9D9] flex justify-center gap-8 text-xs text-amazon-link-teal">
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
