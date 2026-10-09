import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Check, Clock, ExternalLink } from 'lucide-react';
import api from '../api';

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const nav = useNavigate();

  const loadNotifications = () => {
    api.get('/notifications')
      .then(res => setNotifications(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(loadNotifications, []);

  const handleClick = async (n) => {
    if (!n.read) {
      await api.post(`/notifications/${n.id}/read`).catch(() => {});
    }
    if (n.link) {
      nav(n.link);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-2">
            <Bell className="w-6 h-6 text-brand-400" /> Notifications
          </h1>
          <p className="text-slate-400 text-sm">System alerts regarding your item matches and ownership verifications.</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading notifications...</div>
      ) : notifications.length === 0 ? (
        <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 text-slate-400 space-y-3">
          <Bell className="w-10 h-10 mx-auto text-slate-600" />
          <p className="text-sm">You have no notifications right now.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => (
            <div
              key={n.id}
              onClick={() => handleClick(n)}
              className={`glass-panel rounded-2xl p-4 border transition-all cursor-pointer flex items-center justify-between gap-4 ${
                n.read
                  ? 'border-slate-800/80 bg-slate-900/40 hover:bg-slate-900/70 text-slate-300'
                  : 'border-brand-500/40 bg-brand-500/5 hover:bg-brand-500/10 text-white shadow-md'
              }`}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    n.read ? 'bg-slate-700' : 'bg-brand-400 animate-pulse'
                  }`}
                />
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-relaxed">{n.text}</p>
                  <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1.5">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(n.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>

              {n.link && (
                <ExternalLink className="w-4 h-4 text-slate-400 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
