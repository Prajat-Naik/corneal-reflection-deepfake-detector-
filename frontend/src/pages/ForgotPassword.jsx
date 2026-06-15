import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Shield, User, HelpCircle } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function ForgotPassword() {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRequest = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/forgot-password`, { username });
      setMessage(response.data.message);
      setTimeout(() => {
        navigate('/reset-password');
      }, 4000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to request password reset.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-900/20 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-teal-900/20 rounded-full blur-3xl -z-10 animate-pulse delay-700"></div>

      <div className="w-full max-w-md bg-slate-900/50 border border-slate-800 rounded-2xl backdrop-blur-md shadow-2xl p-8">
        <div className="flex flex-col items-center mb-6">
          <div className="w-16 h-16 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl flex items-center justify-center mb-4 text-indigo-400">
            <HelpCircle className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Reset Account Key</h1>
          <p className="text-slate-400 text-sm mt-1">AuraEye Key Recovery Console</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        {message && (
          <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 text-sm p-4 rounded-lg mb-4 leading-relaxed">
            {message}
          </div>
        )}

        <form onSubmit={handleRequest} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Username</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <User className="w-4 h-4" />
              </span>
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter account username"
                className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-white placeholder-slate-650 focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full text-white font-medium py-2 rounded-lg transition-colors flex items-center justify-center gap-2 mt-4"
            style={{ backgroundColor: '#6366f1' }}
          >
            {loading ? 'Consulting registry...' : 'Request Key Reset'}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          Remember key?{' '}
          <Link to="/login" className="text-indigo-400 hover:underline">Log In</Link>
        </p>
      </div>
    </div>
  );
}

export default ForgotPassword;
