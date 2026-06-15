import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { ShieldCheck, ShieldAlert, BarChart3, Clock, ArrowRight } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function UserDashboard() {
  const [stats, setStats] = useState({
    totalAnalyses: 0,
    realDetections: 0,
    deepfakeDetections: 0,
    recentActivity: []
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/user/dashboard`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setStats(response.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to retrieve dashboard logs.');
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Top Header Banner */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight text-white">Auditor Dashboard</h1>
            <p className="text-slate-400 text-sm mt-1">Overview of media authenticity analyses and nodes activities.</p>
          </div>
          <button
            onClick={() => navigate('/workspace')}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-lg text-sm font-semibold shadow-lg shadow-indigo-650/15 flex items-center gap-2 transition-all"
          >
            Audit New Media
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Consulting core ledger...</p>
          </div>
        ) : (
          <>
            {/* Grid Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Total Card */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <BarChart3 className="w-24 h-24 text-white" />
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                    <BarChart3 className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Analyses</p>
                    <h3 className="text-3xl font-extrabold text-white mt-1">{stats.totalAnalyses}</h3>
                  </div>
                </div>
              </div>

              {/* Real Card */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <ShieldCheck className="w-24 h-24 text-emerald-400" />
                </div>
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

              {/* Fake Card */}
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5">
                  <ShieldAlert className="w-24 h-24 text-rose-450" />
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
                    <ShieldAlert className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Deepfake Detections</p>
                    <h3 className="text-3xl font-extrabold text-white mt-1">{stats.deepfakeDetections}</h3>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity Table */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl backdrop-blur-sm p-6">
              <div className="flex items-center gap-2 mb-6">
                <Clock className="w-4 h-4 text-indigo-400" />
                <h2 className="text-white font-bold text-lg">Recent Auditing Activity</h2>
              </div>

              {stats.recentActivity.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-sm">
                  No analyses run yet on this node. Navigate to 'Analyze Media' to start auditing.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-medium">
                        <th className="py-3 px-4">Media File Name</th>
                        <th className="py-3 px-4">Audit Date</th>
                        <th className="py-3 px-4 text-center">Verdict</th>
                        <th className="py-3 px-4 text-center">Confidence</th>
                        <th className="py-3 px-4 text-center">Trust Score</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {stats.recentActivity.map((act) => (
                        <tr key={act.id} className="hover:bg-slate-800/20 text-slate-200">
                          <td className="py-3 px-4 font-mono text-xs max-w-xs truncate">{act.media_name}</td>
                          <td className="py-3 px-4 text-xs text-slate-500">
                            {new Date(act.created_at).toLocaleString()}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                              act.result === 'REAL' 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25' 
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/25'
                            }`}>
                              {act.result}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center font-mono text-xs">{act.confidence.toFixed(2)}%</td>
                          <td className="py-3 px-4 text-center font-bold text-xs">{act.trust_score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

      </main>
    </div>
  );
}

export default UserDashboard;
