import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ShieldCheck, CheckCircle2, Clock, AlertTriangle, KeyRound, ArrowLeft, ArrowRight } from 'lucide-react';
import api, { errMsg } from '../api';

export default function ClaimPage() {
  const { matchId } = useParams();
  const [claim, setClaim] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    api.post(`/matches/${matchId}/claim`)
      .then((res) => {
        if (res.data.status) {
          // Already decided claim
          setResult({
            result: res.data.status,
            handover_code: res.data.handover_code,
            attempts_left: 0
          });
        } else {
          setClaim(res.data);
        }
      })
      .catch((ex) => {
        setErr(errMsg(ex, 'Cannot start ownership verification for this item.'));
      })
      .finally(() => setLoading(false));
  }, [matchId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr('');
    setSubmitting(true);

    try {
      const res = await api.post(`/claims/${claim.claim_id}/answers`, { answers });
      setResult(res.data);
    } catch (ex) {
      setErr(errMsg(ex, 'Failed to submit verification answers.'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-slate-500">Preparing verification challenge...</div>;
  }

  if (err && !claim) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-white">Verification Unavailable</h2>
        <p className="text-sm text-slate-400">{err}</p>
        <Link to="/mine" className="inline-flex items-center gap-1.5 text-xs text-brand-400 hover:underline">
          <ArrowLeft className="w-3.5 h-3.5" /> Return to My Reports
        </Link>
      </div>
    );
  }

  // Verification result screen
  if (result) {
    return (
      <div className="max-w-xl mx-auto px-4 py-12 space-y-6">
        <div className="glass-panel rounded-3xl p-8 border border-slate-800 shadow-2xl text-center space-y-6">
          {result.result === 'approved' && (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center mx-auto glow-green">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold text-white">Ownership Verified!</h1>
                <p className="text-xs text-slate-300 mt-1">
                  Your challenge answers match the finder's recorded private details.
                </p>
              </div>

              {/* Handover Code Display */}
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-700/80 space-y-4">
                <div>
                  <div className="text-[11px] font-mono text-slate-400 uppercase tracking-widest flex items-center justify-center gap-1.5">
                    <KeyRound className="w-4 h-4 text-emerald-400" /> One-Time Handover Code
                  </div>
                  <div className="text-4xl sm:text-5xl font-mono font-black text-emerald-400 tracking-[0.25em] select-all py-2">
                    {result.handover_code}
                  </div>
                  <p className="text-[11px] text-amber-300/80">
                    ⚠️ Save this code. Give it to the finder during handover. Both reports will close once confirmed.
                  </p>
                </div>
                
                {result.handover_instructions && (
                  <div className="pt-4 border-t border-slate-800 text-left">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">Meeting Details & Instructions</div>
                    <div className="text-sm text-slate-300 bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                      {result.handover_instructions}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {result.result === 'under_review' && (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-amber-500/10 border border-amber-500/30 text-amber-400 flex items-center justify-center mx-auto">
                <Clock className="w-8 h-8" />
              </div>
              <h1 className="text-2xl font-extrabold text-white">Under Moderator Review</h1>
              <p className="text-sm text-slate-300 leading-relaxed">
                Your answers partially matched the item's details. A campus moderator has been notified to review your responses.
                You will receive a notification once a decision is made.
              </p>
            </div>
          )}

          {result.result === 'not_verified' && (
            <div className="space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center mx-auto">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <h1 className="text-2xl font-extrabold text-white">Could Not Verify Ownership</h1>
              <p className="text-sm text-slate-300">
                The answers provided do not correspond with the finder's private records.
              </p>
              <div className="text-xs font-mono text-amber-400">
                Attempts Remaining: {result.attempts_left}
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-slate-800">
            <Link
              to="/mine"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> Back to My Reports
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-8 space-y-6">
      <div className="space-y-1">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-brand-500/10 border border-brand-500/30 text-brand-300">
          <ShieldCheck className="w-3.5 h-3.5" /> Ownership Challenge
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Verify Your Item</h1>
        <p className="text-slate-400 text-sm">
          Please answer the questions below to prove ownership. Only the rightful owner will know these private details.
        </p>
      </div>

      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-2xl space-y-6">
        <div className="flex items-center justify-between text-xs pb-3 border-b border-slate-800">
          <span className="text-slate-400">Attempts allowed: 2</span>
          <span className="font-mono text-amber-400 font-bold">
            {claim.attempts_left} Attempt{claim.attempts_left === 1 ? '' : 's'} Remaining
          </span>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {claim.questions.map((q, idx) => (
            <div key={q.key} className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300">
                Question {idx + 1}: {q.question}
              </label>
              <textarea
                required
                rows={2}
                value={answers[q.key] || ''}
                onChange={(e) => setAnswers({ ...answers, [q.key]: e.target.value })}
                placeholder="Be as specific and accurate as you remember..."
                className="w-full p-3 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500 resize-none"
              />
            </div>
          ))}

          {err && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium">
              {err}
            </div>
          )}

          <div className="pt-2 flex items-center justify-between">
            <Link to="/mine" className="text-xs text-slate-400 hover:text-white flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Cancel
            </Link>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2.5 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs shadow-lg shadow-brand-600/30 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? 'Verifying Answers...' : 'Submit Answers'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
