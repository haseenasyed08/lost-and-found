import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { FileText, MapPin, Calendar, Clock, Plus, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';
import api, { getImageUrl } from '../api';

export default function MyReports() {
  const [reports, setReports] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/reports/mine')
      .then(res => setReports(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = reports.filter(r => {
    if (filter === 'lost') return r.type === 'lost';
    if (filter === 'found') return r.type === 'found';
    return true;
  });

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">My Reports</h1>
          <p className="text-slate-400 text-sm">Review your posted lost and found items and track suggested matches.</p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/report/lost"
            className="px-4 py-2 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-md shadow-rose-600/20 flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" /> Report Lost
          </Link>
          <Link
            to="/report/found"
            className="px-4 py-2 rounded-xl bg-emerald-600/90 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-md shadow-emerald-600/20 flex items-center gap-1.5"
          >
            <Plus className="w-3.5 h-3.5" /> Report Found
          </Link>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-3">
        {['all', 'lost', 'found'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all ${
              filter === f
                ? 'bg-brand-500 text-white shadow-md'
                : 'bg-slate-900/60 text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            {f === 'all' ? `All (${reports.length})` : f}
          </button>
        ))}
      </div>

      {/* List */}
      {loading ? (
        <div className="text-center py-12 text-slate-500">Loading your reports...</div>
      ) : filtered.length === 0 ? (
        <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 space-y-4">
          <div className="w-12 h-12 rounded-2xl bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">No reports yet</h3>
            <p className="text-xs text-slate-400 mt-1">Submit a report to start receiving automated match suggestions.</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((r) => {
            const isLost = r.type === 'lost';
            const isClosed = r.status === 'closed';
            const isClaimed = r.status === 'claimed';

            return (
              <Link
                key={r.id}
                to={`/reports/${r.id}`}
                className="glass-panel rounded-2xl p-5 border border-slate-800 hover:border-brand-500/50 transition-all hover:-translate-y-1 shadow-lg flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider border ${
                        isLost
                          ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                          : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      }`}
                    >
                      {r.type}
                    </span>

                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider font-semibold ${
                        isClosed
                          ? 'bg-slate-800 text-slate-400'
                          : isClaimed
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {r.status}
                    </span>
                  </div>

                  {r.images && r.images[0] && (
                    <div className="h-32 w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                      <img
                        src={getImageUrl(r.images[0])}
                        alt={r.description}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                  )}

                  <div>
                    <h3 className="font-bold text-white capitalize text-base group-hover:text-brand-300 transition-colors">
                      {r.color} {r.brand} {r.category}
                    </h3>
                    <p className="text-xs text-slate-300 line-clamp-2 mt-1 leading-relaxed">
                      {r.description}
                    </p>
                  </div>

                  <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800/80">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-brand-400" />
                      <span>{r.place}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      <span>{new Date(r.event_time).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-brand-400 font-semibold">
                  <span>View Details & Matches</span>
                  <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
