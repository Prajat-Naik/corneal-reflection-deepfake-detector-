import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Users, BarChart3, ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function AdminDashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalAnalyses: 0,
    realDetections: 0,
    deepfakeDetections: 0,
    systemAccuracy: 0.0
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAdminStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/admin/dashboard`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(response.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to retrieve administrative logs.');
      } finally {
        setLoading(false);
      }
    };
    fetchAdminStats();
  }, []);

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">System Admin Console</h1>
          <p className="text-slate-400 text-sm mt-1">Global management overview of users, analyses metrics, and accuracy benchmarks.</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Synchronizing dashboard statistics...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            {/* Total Users */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Auditor Nodes</p>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{stats.totalUsers}</h3>
                </div>
              </div>
            </div>

            {/* Total Analyses */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <BarChart3 className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Audits</p>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{stats.totalAnalyses}</h3>
                </div>
              </div>
            </div>

            {/* Real Count */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Real Detections</p>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{stats.realDetections}</h3>
                </div>
              </div>
            </div>

            {/* Fake Count */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-450">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Fake Detections</p>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{stats.deepfakeDetections}</h3>
                </div>
              </div>
            </div>

            {/* System Accuracy */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center text-yellow-400">
                  <Cpu className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">System Accuracy</p>
                  <h3 className="text-3xl font-extrabold text-white mt-1">{stats.systemAccuracy}%</h3>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default AdminDashboard;
