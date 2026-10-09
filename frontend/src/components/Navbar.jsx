import React, { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Search, PlusCircle, Compass, FileText, Bell, ShieldCheck, LogOut, User, Sparkles } from 'lucide-react';
import api from '../api';

export default function Navbar() {
  const nav = useNavigate();
  const location = useLocation();
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');
  const name = localStorage.getItem('name') || 'User';
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (token) {
      api.get('/notifications')
        .then(res => {
          const unread = res.data.filter(n => !n.read).length;
          setUnreadCount(unread);
        })
        .catch(() => {});
    }
  }, [token, location.pathname]);

  const logout = () => {
    localStorage.clear();
    nav('/login');
  };

  const isActive = (path) => {
    return location.pathname === path ? 'text-brand-400 bg-slate-800/80 shadow-sm border border-brand-500/30' : 'text-slate-300 hover:text-white hover:bg-slate-800/40';
  };

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 via-blue-500 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-brand-500/20 group-hover:scale-105 transition-transform duration-200">
              <Compass className="w-5 h-5 text-white animate-spin-slow" />
            </div>
            <div>
              <div className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                Findr<span className="text-brand-400">AI</span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">Lost & Found Intelligence</div>
            </div>
          </Link>

          {/* Navigation links */}
          {token && (
            <nav className="hidden md:flex items-center gap-1">
              <Link to="/" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${isActive('/')}`}>
                <Search className="w-4 h-4" /> Search
              </Link>
              <Link to="/report/lost" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${isActive('/report/lost')}`}>
                <span className="w-2 h-2 rounded-full bg-rose-500"></span> Report Lost
              </Link>
              <Link to="/report/found" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${isActive('/report/found')}`}>
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Report Found
              </Link>
              <Link to="/mine" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${isActive('/mine')}`}>
                <FileText className="w-4 h-4" /> My Reports
              </Link>
              <Link to="/notifications" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 relative ${isActive('/notifications')}`}>
                <Bell className="w-4 h-4" /> Notifications
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-brand-500 text-white animate-pulse">
                    {unreadCount}
                  </span>
                )}
              </Link>
              {role === 'moderator' && (
                <Link to="/admin" className={`px-3 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 text-amber-400 hover:text-amber-300 ${isActive('/admin')}`}>
                  <ShieldCheck className="w-4 h-4" /> Moderator
                </Link>
              )}
            </nav>
          )}

          {/* Right Action */}
          <div className="flex items-center gap-3">
            {token ? (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex flex-col text-right">
                  <span className="text-sm font-semibold text-slate-200">{name}</span>
                  <span className="text-[11px] font-mono text-brand-400 capitalize">{role}</span>
                </div>
                <button
                  onClick={logout}
                  title="Log out"
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-sm font-semibold shadow-md shadow-brand-600/30 transition-all hover:scale-[1.02]"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
