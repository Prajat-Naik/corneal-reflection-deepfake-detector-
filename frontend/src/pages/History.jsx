import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { Search, Filter, Trash2, Download, Clock, AlertTriangle } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';
const BASE_URL = 'http://127.0.0.1:5000';

function History() {
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/analyses`, {
        params: { search, filter },
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to retrieve history logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [filter]); // Fetch automatically when filter changes

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchHistory();
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to permanently delete this forensic analysis record?")) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/analyses/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filter out the deleted row immediately for clean UI transition
      setHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to delete record.');
    }
  };

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Forensic Audit History</h1>
          <p className="text-slate-400 text-sm mt-1">Review historical analyses logs, filter results, and export PDF reports.</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {/* Filter controls */}
        <div className="bg-slate-900/40 border border-slate-800 p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between backdrop-blur-sm">
          <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-500">
              <Search className="w-4 h-4" />
            </span>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by media file name..."
              className="w-full bg-slate-950/65 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <button type="submit" className="hidden">Submit</button>
          </form>

          <div className="flex items-center gap-2 w-full md:w-auto">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-slate-950/65 border border-slate-800 text-sm rounded-lg px-3 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors cursor-pointer w-full md:w-auto"
            >
              <option value="">All Verdicts</option>
              <option value="REAL">Real Only</option>
              <option value="DEEPFAKE">Deepfake Only</option>
            </select>
          </div>
        </div>

        {/* Audit list container */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Consulting core database...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="bg-slate-900/10 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-sm">
            No audit records found matching your filters.
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl backdrop-blur-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-950/40 border-b border-slate-800 text-slate-400 font-medium">
                    {history[0]?.username && <th className="py-3 px-4">Auditor</th>}
                    <th className="py-3 px-4">Media File Name</th>
                    <th className="py-3 px-4">Audit Date</th>
                    <th className="py-3 px-4 text-center">Verdict</th>
                    <th className="py-3 px-4 text-center">Confidence</th>
                    <th className="py-3 px-4 text-center">Trust Score</th>
                    <th className="py-3 px-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 text-slate-200">
                  {history.map((record) => (
                    <tr key={record.id} className="hover:bg-slate-800/15 transition-all">
                      {record.username && (
                        <td className="py-3.5 px-4 font-bold text-xs text-indigo-400">{record.username}</td>
                      )}
                      <td className="py-3.5 px-4 font-mono text-xs max-w-xs truncate">{record.media_name}</td>
                      <td className="py-3.5 px-4 text-xs text-slate-500">
                        {new Date(record.created_at).toLocaleString()}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold ${
                          record.result === 'REAL' 
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25' 
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/25'
                        }`}>
                          {record.result}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-center font-mono text-xs">{record.confidence.toFixed(2)}%</td>
                      <td className="py-3.5 px-4 text-center font-bold text-xs">{record.trust_score}</td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center justify-center gap-3">
                          {record.report_path && (
                            <a
                              href={`${BASE_URL}${record.report_path}`}
                              download
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-slate-400 hover:text-indigo-400 p-1 transition-colors"
                              title="Download Report"
                            >
                              <Download className="w-4 h-4" />
                            </a>
                          )}
                          <button
                            onClick={() => handleDelete(record.id)}
                            className="text-slate-400 hover:text-red-400 p-1 transition-colors"
                            title="Delete Record"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default History;
