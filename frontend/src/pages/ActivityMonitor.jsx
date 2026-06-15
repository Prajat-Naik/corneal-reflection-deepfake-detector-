import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Terminal, Clock, Activity } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function ActivityMonitor() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}/admin/monitoring`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setLogs(response.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to retrieve activity monitor logs.');
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getActionColor = (action) => {
    if (action.includes('REGISTER')) return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
    if (action.includes('LOGIN')) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (action.includes('ANALYZE')) return 'text-sky-400 bg-sky-500/10 border-sky-500/20';
    if (action.includes('DELETE') || action.includes('TOGGLE')) return 'text-rose-450 bg-rose-500/10 border-rose-500/20';
    return 'text-slate-400 bg-slate-500/10 border-slate-500/20';
  };

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">System Activity Monitor</h1>
          <p className="text-slate-400 text-sm mt-1">Live tracking of actions taken by active system nodes.</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Consulting ledger audit trail logs...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="bg-slate-900/10 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-sm">
            No system activity logs found.
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl backdrop-blur-sm p-6 space-y-6">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-4">
              <Terminal className="w-5 h-5 text-indigo-400" />
              <h2 className="text-white font-bold text-lg">Live Auditor Actions Log</h2>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {logs.map((log) => (
                <div key={log.id} className="border border-slate-850 bg-slate-950/20 p-4 rounded-xl flex items-center justify-between gap-6 hover:bg-slate-850/10 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-indigo-400">
                      <Activity className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-white font-semibold text-sm">{log.username || 'System Seed'}</span>
                        <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${getActionColor(log.action)}`}>
                          {log.action}
                        </span>
                      </div>
                      <p className="text-slate-400 text-xs mt-1.5 leading-relaxed">{log.details}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(log.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default ActivityMonitor;
