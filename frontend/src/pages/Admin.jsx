import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend
} from 'recharts';
import {
  ShieldCheck, AlertTriangle, CheckCircle2, XCircle, TrendingUp,
  MapPin, Clock, BarChart3, Users, PackageCheck, Flag
} from 'lucide-react';
import api, { errMsg } from '../api';

const COLORS = ['#0c87eb', '#38bdf8', '#818cf8', '#a855f7', '#ec4899', '#f43f5e', '#f97316', '#eab308'];

export default function Admin() {
  const [queue, setQueue] = useState([]);
  const [stats, setStats] = useState(null);
  const [abuseReports, setAbuseReports] = useState([]);
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics', 'queue', 'abuse'
  const [actionMsg, setActionMsg] = useState('');
  const [loading, setLoading] = useState(true);

  const loadAll = () => {
    Promise.all([
      api.get('/admin/analytics').then(r => setStats(r.data)).catch(() => {}),
      api.get('/admin/queue').then(r => setQueue(r.data)).catch(() => setQueue([])),
      api.get('/admin/abuse').then(r => setAbuseReports(r.data)).catch(() => setAbuseReports([])),
    ]).finally(() => setLoading(false));
  };

  useEffect(loadAll, []);

  const handleDecision = async (cid, decision) => {
    setActionMsg('');
    try {
      await api.post(`/admin/claims/${cid}/decision`, { decision });
      setActionMsg(`Claim successfully ${decision}. Claimant and finder have been notified.`);
      loadAll();
    } catch (ex) {
      alert(errMsg(ex, 'Could not record decision'));
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-slate-500">Loading moderator console & analytics...</div>;
  }

  // Format category data for dual bar chart
  const categoryChartData = stats?.by_category?.reduce((acc, cur) => {
    let existing = acc.find(item => item.category === cur.category);
    if (!existing) {
      existing = { category: cur.category, lost: 0, found: 0 };
      acc.push(existing);
    }
    if (cur.type === 'lost') existing.lost += cur.count;
    if (cur.type === 'found') existing.found += cur.count;
    return acc;
  }, []) || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Console Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 border border-amber-500/30 text-amber-300 mb-2">
            <ShieldCheck className="w-3.5 h-3.5" /> Campus Moderator Control Center
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Intelligence & Operations Console</h1>
          <p className="text-slate-400 text-sm">
            Monitor recovery analytics, resolve manual review ownership claims, and maintain platform security.
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex bg-slate-900 border border-slate-800 p-1 rounded-2xl">
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'analytics'
                ? 'bg-brand-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-4 h-4" /> Analytics
          </button>
          <button
            onClick={() => setActiveTab('queue')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 relative ${
              activeTab === 'queue'
                ? 'bg-brand-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="w-4 h-4" /> Claim Queue
            {queue.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-amber-400 text-slate-950 font-black">
                {queue.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('abuse')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
              activeTab === 'abuse'
                ? 'bg-brand-500 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Flag className="w-4 h-4" /> Flagged ({abuseReports.length})
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" /> {actionMsg}
        </div>
      )}

      {/* TAB 1: ANALYTICS DASHBOARD */}
      {activeTab === 'analytics' && stats && (
        <div className="space-y-8">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>Recovery Rate</span>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-3xl font-extrabold text-white">
                {Math.round(stats.recovery_rate * 100)}%
              </div>
              <p className="text-[11px] text-slate-400">
                {stats.lost_closed} closed of {stats.lost_total} lost reports
              </p>
            </div>

            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>Median Recovery Time</span>
                <Clock className="w-4 h-4 text-brand-400" />
              </div>
              <div className="text-3xl font-extrabold text-white font-mono">
                {stats.median_hours_to_recovery ? `${stats.median_hours_to_recovery}h` : 'N/A'}
              </div>
              <p className="text-[11px] text-slate-400">From submission to confirmed return</p>
            </div>

            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>Total Items Tracked</span>
                <PackageCheck className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-3xl font-extrabold text-white">
                {stats.lost_total + stats.found_total}
              </div>
              <p className="text-[11px] text-slate-400">
                {stats.lost_total} lost, {stats.found_total} found
              </p>
            </div>

            <div className="glass-panel rounded-2xl p-5 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
                <span>AI Suggested Matches</span>
                <ShieldCheck className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-3xl font-extrabold text-white font-mono">
                {stats.matches_total}
              </div>
              <p className="text-[11px] text-slate-400">Computed via multi-factor engine</p>
            </div>
          </div>

          {/* Charts Row 1: Hotspots & Category Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Hotspots Chart */}
            <div className="glass-panel rounded-3xl p-6 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-rose-400" /> Campus Hotspots (Lost Reports)
                  </h3>
                  <p className="text-xs text-slate-400">Locations with highest reported loss frequency</p>
                </div>
              </div>

              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.hotspots.slice(0, 8)} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                    <XAxis
                      dataKey="place"
                      angle={-35}
                      textAnchor="end"
                      height={60}
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                    />
                    <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                      itemStyle={{ color: '#38bdf8' }}
                    />
                    <Bar dataKey="count" fill="#38bdf8" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Category Lost vs Found Breakdown */}
            <div className="glass-panel rounded-3xl p-6 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <PackageCheck className="w-4 h-4 text-brand-400" /> Item Category Breakdown
                  </h3>
                  <p className="text-xs text-slate-400">Lost vs Found volume per category</p>
                </div>
              </div>

              <div className="h-72 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoryChartData.slice(0, 7)} margin={{ top: 10, right: 10, left: -20, bottom: 40 }}>
                    <XAxis
                      dataKey="category"
                      angle={-35}
                      textAnchor="end"
                      height={60}
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                    />
                    <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                    />
                    <Legend wrapperStyle={{ paddingTop: '10px' }} />
                    <Bar dataKey="lost" name="Lost Items" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="found" name="Found Items" fill="#10b981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Daily Timeline */}
          {stats.daily && stats.daily.length > 0 && (
            <div className="glass-panel rounded-3xl p-6 border border-slate-800 shadow-xl space-y-4">
              <h3 className="text-base font-bold text-white">Daily Report Activity</h3>
              <div className="h-60 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.daily} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                    <YAxis allowDecimals={false} tick={{ fill: '#94a3b8', fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }} />
                    <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MANUAL REVIEW CLAIMS QUEUE */}
      {activeTab === 'queue' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-amber-400" /> Claims Pending Moderator Review ({queue.length})
            </h2>
            <span className="text-xs text-slate-400">2 of 3 questions matched criteria</span>
          </div>

          {queue.length === 0 ? (
            <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 text-slate-400 space-y-3">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
              <h3 className="font-bold text-white text-base">Claim Queue is Clear</h3>
              <p className="text-xs text-slate-400">All submitted claims have been processed automatically or decided.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {queue.map((c) => (
                <div key={c.claim_id} className="glass-panel rounded-3xl p-6 border border-amber-500/30 shadow-2xl space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div>
                      <span className="text-xs font-mono text-amber-400 uppercase tracking-wider font-bold">
                        Claim #{c.claim_id}
                      </span>
                      <h3 className="font-extrabold text-white text-lg mt-0.5">
                        {c.found.color} {c.found.brand} {c.found.category}
                      </h3>
                    </div>
                    <span className="text-xs text-slate-400 font-mono">
                      Submitted: {new Date(c.created_at).toLocaleString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                      <span className="font-bold text-emerald-400 uppercase tracking-wider text-[10px]">Found Report Description</span>
                      <p className="text-slate-300 leading-relaxed">{c.found.description}</p>
                      <span className="text-[11px] text-slate-400 block pt-1">Found at: {c.found.place}</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                      <span className="font-bold text-rose-400 uppercase tracking-wider text-[10px]">Lost Report Description</span>
                      <p className="text-slate-300 leading-relaxed">{c.lost.description}</p>
                      <span className="text-[11px] text-slate-400 block pt-1">Lost at: {c.lost.place}</span>
                    </div>
                  </div>

                  {/* Question and Answer Table */}
                  <div className="overflow-x-auto rounded-2xl border border-slate-800">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                        <tr>
                          <th className="p-3.5 font-semibold">Private Verification Question</th>
                          <th className="p-3.5 font-semibold text-emerald-400">Finder's Recorded Detail</th>
                          <th className="p-3.5 font-semibold text-brand-300">Claimant's Given Answer</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {c.rows.map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40">
                            <td className="p-3.5 font-medium text-slate-300">{row.question}</td>
                            <td className="p-3.5 font-mono text-emerald-300 bg-emerald-500/5">{row.finder_detail}</td>
                            <td className="p-3.5 font-mono text-slate-200 bg-brand-500/5">{row.claimant_answer || '(Blank)'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Decision Actions */}
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => handleDecision(c.claim_id, 'rejected')}
                      className="px-5 py-2.5 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-bold transition-all flex items-center gap-1.5"
                    >
                      <XCircle className="w-4 h-4" /> Reject Claim
                    </button>
                    <button
                      onClick={() => handleDecision(c.claim_id, 'approved')}
                      className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-lg shadow-emerald-600/20 flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-4 h-4" /> Approve Ownership & Issue Code
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: FLAGGED ABUSE REPORTS */}
      {activeTab === 'abuse' && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Flag className="w-5 h-5 text-rose-400" /> Flagged Abuse Reports ({abuseReports.length})
          </h2>

          {abuseReports.length === 0 ? (
            <div className="glass-panel rounded-3xl p-12 text-center border border-slate-800 text-slate-400">
              No reports have been flagged for abuse.
            </div>
          ) : (
            <div className="space-y-3">
              {abuseReports.map((a) => (
                <div key={a.id} className="glass-panel rounded-2xl p-4 border border-rose-500/30 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-rose-400">Flag on Report #{a.report_id}</span>
                    <p className="text-slate-300 mt-1">{a.reason}</p>
                    <span className="text-[10px] text-slate-400 font-mono mt-1 block">{new Date(a.created_at).toLocaleString()}</span>
                  </div>
                  <a href={`/reports/${a.report_id}`} className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-200 hover:text-white font-semibold">
                    Inspect Report
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
