import React, { useEffect, useState } from 'react';
import axios from 'axios';
import Sidebar from '../components/Sidebar';
import { User, ShieldAlert, Check, Ban, Trash2, Calendar } from 'lucide-react';

const API_URL = 'http://127.0.0.1:5000/api';

function UserManagement() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch user directory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleToggleStatus = async (id, currentStatus) => {
    const nextStatus = currentStatus === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`${API_URL}/admin/users/${id}/status`, { status: nextStatus }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(prev => prev.map(u => u.id === id ? { ...u, status: nextStatus } : u));
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to update user status.');
    }
  };

  const handleDeleteUser = async (id, name) => {
    if (!window.confirm(`Are you sure you want to permanently delete user account '${name}' and all associated history logs?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/admin/users/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to delete user.');
    }
  };

  return (
    <div className="min-h-screen pl-64 bg-cyber-dark text-slate-100">
      <Sidebar />
      <main className="p-8 max-w-7xl mx-auto space-y-8">
        
        {/* Header Title */}
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">Auditor Node Directory</h1>
          <p className="text-slate-400 text-sm mt-1">Manage system nodes, toggle active status, and delete registries.</p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-200 text-sm p-4 rounded-xl">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="w-10 h-10 border-4 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm">Consulting node registry list...</p>
          </div>
        ) : users.length === 0 ? (
          <div className="bg-slate-900/10 border border-slate-800 rounded-xl p-12 text-center text-slate-500 text-sm">
            No registered auditor nodes found in database.
          </div>
        ) : (
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl backdrop-blur-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="bg-slate-950/40 border-b border-slate-800 text-slate-400 font-medium">
                    <th className="py-3 px-4">Node Account</th>
                    <th className="py-3 px-4">Role Designation</th>
                    <th className="py-3 px-4">Registry Date</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 text-slate-200">
                  {users.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/15 transition-all">
                      <td className="py-3.5 px-4 font-bold text-slate-200 flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 text-xs">
                          {item.username.substring(0, 2).toUpperCase()}
                        </div>
                        {item.username}
                      </td>
                      <td className="py-3.5 px-4 text-xs font-semibold text-slate-400 font-mono">{item.role}</td>
                      <td className="py-3.5 px-4 text-xs text-slate-500">
                        {new Date(item.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          item.status === 'ACTIVE' 
                            ? 'bg-emerald-500/10 text-emerald-450 border border-emerald-500/20' 
                            : 'bg-yellow-500/10 text-yellow-450 border border-yellow-500/20'
                        }`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center justify-center gap-3">
                          <button
                            onClick={() => handleToggleStatus(item.id, item.status)}
                            className={`p-1.5 rounded-lg border transition-colors ${
                              item.status === 'ACTIVE'
                                ? 'border-yellow-500/20 bg-yellow-500/5 text-yellow-550 hover:bg-yellow-500/10'
                                : 'border-emerald-500/20 bg-emerald-500/5 text-emerald-450 hover:bg-emerald-500/10'
                            }`}
                            title={item.status === 'ACTIVE' ? 'Deactivate User' : 'Activate User'}
                          >
                            {item.status === 'ACTIVE' ? <Ban className="w-3.5 h-3.5" /> : <Check className="w-3.5 h-3.5" />}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(item.id, item.username)}
                            className="p-1.5 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Delete Node"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
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

export default UserManagement;
