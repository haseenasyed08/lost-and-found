import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  MapPin, Calendar, Clock, ShieldCheck, CheckCircle2,
  XCircle, AlertTriangle, ArrowRight, KeyRound, Flag, Eye
} from 'lucide-react';
import api, { getImageUrl, errMsg } from '../api';
import SignalBar from '../components/SignalBar';

const CONFIDENCE_BADGE = {
  high: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  medium: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
  low: 'bg-slate-500/20 text-slate-400 border-slate-500/40',
};

export default function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [matches, setMatches] = useState([]);
  const [handoverCode, setHandoverCode] = useState('');
  const [confirmMsg, setConfirmMsg] = useState('');
  const [confirmErr, setConfirmErr] = useState('');
  const [abuseReason, setAbuseReason] = useState('');
  const [showAbuseModal, setShowAbuseModal] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    api.get(`/reports/${id}`)
      .then(res => setReport(res.data))
      .catch(() => {});

    api.get(`/reports/${id}/matches`)
      .then(res => setMatches(res.data))
      .catch(() => setMatches([]))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, [id]);

  const handleDismiss = async (mid) => {
    try {
      await api.post(`/reports/matches/${mid}/dismiss`);
      loadData();
    } catch (ex) {
      alert(errMsg(ex, 'Could not dismiss match'));
    }
  };

  const handleConfirmHandover = async (cid) => {
    setConfirmMsg('');
    setConfirmErr('');
    try {
      const res = await api.post(`/claims/${cid}/confirm`, { code: handoverCode });
      setConfirmMsg(res.data.message || 'Handover successfully confirmed! Both reports are now closed.');
      setHandoverCode('');
      loadData();
    } catch (ex) {
      setConfirmErr(errMsg(ex, 'Invalid handover code. Please check with the owner.'));
    }
  };

  const handleReportAbuse = async () => {
    if (!abuseReason.trim()) return;
    try {
      await api.post(`/reports/${id}/abuse`, { reason: abuseReason });
      setShowAbuseModal(false);
      setAbuseReason('');
      alert('Report flagged for moderator review.');
    } catch (ex) {
      alert(errMsg(ex, 'Could not submit report'));
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-slate-500">Loading item details...</div>;
  }

  if (!report) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center text-slate-400">
        Report not found or access denied.
      </div>
    );
  }

  const isLost = report.type === 'lost';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Main Item Detail Card */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border ${
                isLost ? 'bg-rose-500/10 border-rose-500/30 text-rose-300' : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              }`}>
                {report.type} report
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                Status: {report.status}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white capitalize">
              {report.color} {report.brand} {report.category}
            </h1>
          </div>

          <button
            onClick={() => setShowAbuseModal(true)}
            className="self-start sm:self-auto text-xs text-slate-400 hover:text-rose-400 flex items-center gap-1.5 p-2 rounded-lg hover:bg-slate-800/60 transition-colors"
          >
            <Flag className="w-3.5 h-3.5" /> Flag abuse
          </button>
        </div>

        {/* Photos */}
        {report.images && report.images.length > 0 && (
          <div className="flex gap-4 overflow-x-auto py-2">
            {report.images.map((img, i) => (
              <div key={i} className="relative h-48 w-64 rounded-2xl overflow-hidden border border-slate-800 bg-slate-950 flex-shrink-0">
                <img src={getImageUrl(img)} alt="Report photo" className="w-full h-full object-cover" />
                <span className="absolute bottom-2 left-2 text-[10px] font-mono bg-black/70 px-2 py-0.5 rounded-md text-slate-300">
                  Privacy Protected Photo
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Description */}
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</h3>
          <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
            {report.description}
          </p>
        </div>

        {/* Meta details */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-center gap-3">
            <MapPin className="w-4 h-4 text-brand-400" />
            <div>
              <div className="text-[11px] text-slate-400">Reported Place</div>
              <div className="text-xs font-semibold text-white">{report.place}</div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-center gap-3">
            <Calendar className="w-4 h-4 text-purple-400" />
            <div>
              <div className="text-[11px] text-slate-400">Event Date & Time</div>
              <div className="text-xs font-semibold text-white">{new Date(report.event_time).toLocaleString()}</div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-center gap-3">
            <Clock className="w-4 h-4 text-emerald-400" />
            <div>
              <div className="text-[11px] text-slate-400">Created In System</div>
              <div className="text-xs font-semibold text-white">{new Date(report.created_at).toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Suggested Matches Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-brand-400" /> Potential AI Matches ({matches.length})
            </h2>
            <p className="text-xs text-slate-400">
              The system suggests candidate matches. Ownership must be verified before releasing the item.
            </p>
          </div>
        </div>

        {matches.length === 0 ? (
          <div className="glass-panel rounded-2xl p-8 text-center text-slate-400 border border-slate-800">
            No suggestions yet. The engine continuously searches whenever new items are reported.
          </div>
        ) : (
          <div className="space-y-4">
            {matches.map((m) => {
              const other = m.other;
              const hasApprovedClaim = Boolean(m.claim_id);

              return (
                <div
                  key={m.match_id}
                  className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800 shadow-xl space-y-4 hover:border-slate-700 transition-colors"
                >
                  {/* Match Item Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                    <div className="flex items-center gap-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${CONFIDENCE_BADGE[m.confidence] || CONFIDENCE_BADGE.low}`}>
                        {m.confidence} Confidence
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        Overall Score: <b className="text-brand-400">{(m.score * 100).toFixed(1)}%</b>
                      </span>
                    </div>

                    <div className="text-xs text-slate-400">
                      Match Status: <span className="font-mono uppercase text-slate-300 font-semibold">{m.status}</span>
                    </div>
                  </div>

                  {/* Other Item Preview */}
                  <div className="flex flex-col sm:flex-row gap-4 items-start">
                    {other.images && other.images[0] && (
                      <div className="h-28 w-28 rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex-shrink-0">
                        <img src={getImageUrl(other.images[0])} alt="Match photo" className="w-full h-full object-cover" />
                      </div>
                    )}
                    <div className="flex-1 space-y-1.5">
                      <h3 className="font-bold text-white capitalize text-base">
                        {other.color} {other.brand} {other.category}
                      </h3>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {other.description}
                      </p>
                      <div className="text-xs text-slate-400 flex flex-wrap gap-4 pt-1">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-brand-400" /> {other.place}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5 text-slate-500" /> {new Date(other.event_time).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Component Signal Breakdown */}
                  <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-1">
                    <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-1">
                      Multi-Factor Signal Breakdown
                    </div>
                    {Object.entries(m.components).map(([k, v]) => (
                      <SignalBar key={k} signalKey={k} value={v} />
                    ))}
                  </div>

                  {/* Actions Bar */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    {/* Lost side: Start Claim / Ownership Verification */}
                    {isLost && m.status === 'suggested' && (
                      <Link
                        to={`/claim/${m.match_id}`}
                        className="px-5 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-md shadow-brand-600/30 transition-all flex items-center gap-1.5"
                      >
                        <ShieldCheck className="w-4 h-4" /> Start Ownership Verification
                      </Link>
                    )}

                    {/* Found side: Handover Code confirmation if owner passed verification */}
                    {!isLost && hasApprovedClaim && (
                      <div className="w-full p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-3">
                        <div className="flex items-center gap-2 text-emerald-300 font-bold text-xs">
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Owner Passed Verification! Complete Handover
                        </div>
                        <p className="text-xs text-slate-300">
                          Ask the owner for their 6-digit one-time handover code and enter it below to close both reports.
                        </p>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            maxLength={6}
                            placeholder="6-digit code"
                            value={handoverCode}
                            onChange={(e) => setHandoverCode(e.target.value)}
                            className="w-36 px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white font-mono text-center tracking-widest text-sm focus:outline-none focus:border-brand-500"
                          />
                          <button
                            onClick={() => handleConfirmHandover(m.claim_id)}
                            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all"
                          >
                            Confirm Handover
                          </button>
                        </div>
                        {confirmErr && <p className="text-rose-400 text-xs font-medium">{confirmErr}</p>}
                        {confirmMsg && <p className="text-emerald-400 text-xs font-medium">{confirmMsg}</p>}
                      </div>
                    )}

                    {m.status === 'suggested' && (
                      <button
                        onClick={() => handleDismiss(m.match_id)}
                        className="text-xs text-slate-400 hover:text-slate-200 underline transition-colors"
                      >
                        Dismiss (Not a Match)
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Abuse Modal */}
      {showAbuseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="glass-panel max-w-md w-full rounded-2xl p-6 border border-slate-800 space-y-4">
            <h3 className="font-bold text-white text-lg">Report Inappropriate or Suspicious Report</h3>
            <textarea
              rows={3}
              value={abuseReason}
              onChange={(e) => setAbuseReason(e.target.value)}
              placeholder="State the reason (spam, false information, offensive content)..."
              className="w-full p-3 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAbuseModal(false)}
                className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleReportAbuse}
                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold"
              >
                Submit Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
