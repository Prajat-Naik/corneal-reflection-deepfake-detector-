import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Terminal, Lock, User, Eye, EyeOff } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function AdminLogin() {
  const [adminId, setAdminId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/admin/login`, { adminId, password });
      
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Admin authentication failed. Access denied.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-slate-950">
      {/* Background neon lines/glow effects */}
      <div className="absolute top-1/3 left-1/3 w-96 h-96 bg-purple-900/20 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-1/3 right-1/3 w-96 h-96 bg-rose-900/10 rounded-full blur-3xl -z-10 animate-pulse delay-1000"></div>

      <div className="w-full max-w-md bg-slate-900/60 border border-red-500/20 rounded-2xl backdrop-blur-md shadow-2xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center justify-center mb-4 text-red-400">
            <Terminal className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">AuraEye Admin</h1>
          <p className="text-red-400 text-xs font-semibold uppercase tracking-widest mt-1">Administrative Console</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Admin Username / ID</label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <User className="w-4 h-4" />
              </span>
              <input
                type="text"
                required
                value={adminId}
                onChange={(e) => setAdminId(e.target.value)}
                placeholder="Enter admin identifier"
                className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-red-500 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Password</label>
            </div>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••"
                className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-10 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-red-500 transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-350"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-4"
            style={{ backgroundColor: '#ef4444' }}
          >
            {loading ? 'Verifying admin clearance...' : 'Access Admin Console'}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          Accessing unauthorized area is audited.{' '}
          <Link to="/login" className="text-indigo-400 hover:underline">User Login</Link>
        </p>
      </div>
    </div>
  );
}

export default AdminLogin;
