import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Shield, Lock, Mail, Eye, EyeOff, Terminal, User } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  // Determine starting tab based on URL path (support both /login and /admin/login)
  const isAdminPath = location.pathname.includes('/admin');
  const [activeTab, setActiveTab] = useState(isAdminPath ? 'admin' : 'user');

  // Form input states
  const [email, setEmail] = useState('');
  const [userPassword, setUserPassword] = useState('');
  const [adminId, setAdminId] = useState('');
  const [adminPassword, setAdminPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Reset password visibility and error when toggling tabs
  useEffect(() => {
    setError('');
    setShowPassword(false);
  }, [activeTab]);

  const handleUserLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/login`, { 
        username: email, 
        password: userPassword 
      });
      
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/auth/admin/login`, { 
        adminId: adminId, 
        password: adminPassword 
      });
      
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.response?.data?.message || 'Admin access verification failed. Access denied.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden bg-slate-950">
      {/* Background glow effects - color shifts based on active tab */}
      <div className={`absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl -z-10 animate-pulse transition-all duration-700 ${
        activeTab === 'user' ? 'bg-indigo-900/20' : 'bg-rose-900/10'
      }`}></div>
      <div className={`absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-3xl -z-10 animate-pulse delay-700 transition-all duration-700 ${
        activeTab === 'user' ? 'bg-teal-900/20' : 'bg-purple-900/10'
      }`}></div>

      <div className={`w-full max-w-md bg-slate-900/50 border rounded-2xl backdrop-blur-md shadow-2xl p-8 transition-all duration-500 ${
        activeTab === 'user' ? 'border-indigo-500/20' : 'border-red-500/20'
      }`}>
        
        {/* Header Header Icon/Info */}
        <div className="flex flex-col items-center mb-6">
          <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 border transition-all duration-500 ${
            activeTab === 'user' 
              ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' 
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {activeTab === 'user' ? <Shield className="w-8 h-8" /> : <Terminal className="w-8 h-8" />}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">AuraEye Forensics</h1>
          <p className="text-slate-400 text-sm mt-1">Deepfake Specular Reflection Analyzer</p>
        </div>

        {/* Tab Selectors */}
        <div className="flex border-b border-slate-800 mb-6">
          <button
            type="button"
            onClick={() => setActiveTab('user')}
            className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'user'
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-400'
            }`}
          >
            User Portal
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('admin')}
            className={`flex-1 pb-3 text-sm font-semibold border-b-2 transition-all ${
              activeTab === 'admin'
                ? 'border-red-500 text-red-400 font-bold'
                : 'border-transparent text-slate-500 hover:text-slate-400'
            }`}
          >
            Admin Console
          </button>
        </div>

        {/* Dynamic Errors */}
        {error && (
          <div className={`border text-sm p-3 rounded-lg mb-6 transition-colors duration-500 ${
            activeTab === 'user' 
              ? 'bg-red-500/10 border-red-500/20 text-red-200' 
              : 'bg-red-500/15 border-red-500/30 text-red-100'
          }`}>
            {error}
          </div>
        )}

        {/* Tab 1: User Login Form */}
        {activeTab === 'user' && (
          <form onSubmit={handleUserLogin} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Email Address</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <Mail className="w-4 h-4" />
                </span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter email address"
                  className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Password</label>
                <Link to="/forgot-password" className="text-xs text-indigo-400 hover:underline">Forgot Password?</Link>
              </div>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={userPassword}
                  onChange={(e) => setUserPassword(e.target.value)}
                  placeholder="••••••"
                  className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-10 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-300"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-550 active:bg-indigo-700 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-4"
              style={{ backgroundColor: '#6366f1' }}
            >
              {loading ? 'Decrypting credentials...' : 'Access Portal'}
            </button>
          </form>
        )}

        {/* Tab 2: Admin Login Form */}
        {activeTab === 'admin' && (
          <form onSubmit={handleAdminLogin} className="space-y-5">
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
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  placeholder="••••••"
                  className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-10 py-2.5 text-white placeholder-slate-600 focus:outline-none focus:border-red-500 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-300"
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
        )}

        {/* Footer/Navigation Info */}
        <div className="text-center text-slate-500 text-sm mt-6">
          {activeTab === 'user' ? (
            <>
              Authorized auditor registration required.{' '}
              <Link to="/register" className="text-indigo-400 hover:underline">Register Account</Link>
            </>
          ) : (
            <span className="text-xs font-mono text-red-500/70">
              Accessing unauthorized console is monitored and logged.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default Login;
