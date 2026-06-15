import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { BarChart3, PieChart as PieIcon, LineChart as LineIcon, AreaChart as AreaIcon } from 'lucide-react';
import { 
  PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, BarChart, Bar, 
  AreaChart, Area, ResponsiveContainer 
} from 'recharts';

const API_URL = 'http://127.0.0.1:5000/api';

function AdminStats() {
  const [data, setData] = useState({
    realVsFake: [],
    monthlyAnalyses: [],
    confidenceDistribution: [],
    trustScoreDistribution: []
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/admin/statistics`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setData(response.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to retrieve stats graphics.');
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const COLORS = ['#10b981', '#ef4444']; // Green for Real, Red for Fake

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">System Performance Statistics</h1>
          <p className="text-slate-400 text-sm mt-1">Audit trends, confidence levels, and trust score density maps.</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Rendering statistical charts...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Chart 1: Real vs Deepfake counts */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <PieIcon className="w-4 h-4 text-indigo-400" />
                <h3 className="text-white font-bold text-base">Real vs Deepfake Ratio</h3>
              </div>
              <div className="h-64 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.realVsFake}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {data.realVsFake.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', color: '#fff' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Monthly Analysis Counts */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <LineIcon className="w-4 h-4 text-indigo-400" />
                <h3 className="text-white font-bold text-base">Monthly Analysis Activity</h3>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.monthlyAnalyses}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="month" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', color: '#fff' }} />
                    <Legend />
                    <Line type="monotone" dataKey="analyses" stroke="#6366f1" strokeWidth={2} activeDot={{ r: 8 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 3: Confidence Distribution */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                <h3 className="text-white font-bold text-base">Confidence Score Distribution</h3>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.confidenceDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="range" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', color: '#fff' }} />
                    <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 4: Trust Score Density */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 backdrop-blur-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                <AreaIcon className="w-4 h-4 text-indigo-400" />
                <h3 className="text-white font-bold text-base">Trust Score Classification Density</h3>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.trustScoreDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="range" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip contentStyle={{ backgroundColor: '#0b0f19', borderColor: '#1e293b', color: '#fff' }} />
                    <Area type="monotone" dataKey="count" stroke="#a78bfa" fill="#a78bfa" fillOpacity={0.15} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

          </div>
        )}

      </main>
    </div>
  );
}

export default AdminStats;
