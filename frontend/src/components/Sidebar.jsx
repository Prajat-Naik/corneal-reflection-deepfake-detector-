import React from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { 
  LayoutDashboard, UploadCloud, History, 
  Users, Terminal, BarChart3, LogOut, Shield 
} from 'lucide-react';

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : { username: 'Guest', role: 'USER' };
  const role = user.role;

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const userMenuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Analyze Media', path: '/workspace', icon: UploadCloud },
    { name: 'Audit History', path: '/history', icon: History },
  ];

  const adminMenuItems = [
    { name: 'Admin Dashboard', path: '/admin/dashboard', icon: LayoutDashboard },
    { name: 'User Directory', path: '/admin/users', icon: Users },
    { name: 'Global Audit Logs', path: '/history', icon: History },
    { name: 'Activity Monitor', path: '/admin/activities', icon: Terminal },
    { name: 'System Statistics', path: '/admin/stats', icon: BarChart3 },
  ];

  const menuItems = role === 'ADMIN' ? adminMenuItems : userMenuItems;

  return (
    <div className="w-64 bg-slate-900/60 border-r border-slate-800 h-screen flex flex-col fixed left-0 top-0 backdrop-blur-md z-30">
      {/* Sidebar Header Title */}
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-10 h-10 bg-indigo-500/10 border border-indigo-500/30 rounded-xl flex items-center justify-center text-indigo-400">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-white font-bold text-sm tracking-wide">AuraEye Admin</h2>
          <span className="text-slate-500 text-xs uppercase tracking-wider font-semibold">{role} Node</span>
        </div>
      </div>

      {/* Nav Menu Items */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive 
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-650/10' 
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Profile & Logout Footer */}
      <div className="p-4 border-t border-slate-800 flex flex-col gap-3 bg-slate-950/20">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 uppercase text-xs">
            {user.username.substring(0, 2)}
          </div>
          <div className="overflow-hidden">
            <p className="text-white text-xs font-semibold truncate">{user.username}</p>
            <p className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">{user.role}</p>
          </div>
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center gap-2 border border-slate-800 hover:border-red-500/30 hover:bg-red-500/5 text-slate-400 hover:text-red-400 py-2 rounded-lg text-xs font-semibold transition-all mt-1"
        >
          <LogOut className="w-3.5 h-3.5" />
          Terminate Session
        </button>
      </div>
    </div>
  );
}

export default Sidebar;
