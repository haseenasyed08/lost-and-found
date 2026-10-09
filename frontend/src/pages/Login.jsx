import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, Lock, Mail, User, ShieldCheck, ArrowRight, Sparkles } from 'lucide-react';
import api, { errMsg } from '../api';

export default function Login() {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', name: '' });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const nav = useNavigate();

  const handleChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setErr('');
    setLoading(true);
    try {
      const res = mode === 'login'
        ? await api.post('/auth/login', { username: form.email, password: form.password })
        : await api.post('/auth/register', form);

      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      localStorage.setItem('name', res.data.name);
      localStorage.setItem('email', form.email);
      nav('/');
    } catch (ex) {
      setErr(errMsg(ex, 'Authentication failed. Please check your credentials.'));
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = async (email, password) => {
    setErr('');
    setLoading(true);
    try {
      const res = await api.post('/auth/login', { username: email, password });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      localStorage.setItem('name', res.data.name);
      localStorage.setItem('email', email);
      nav('/');
    } catch (ex) {
      setErr(errMsg(ex, 'Demo login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 via-blue-500 to-indigo-500 flex items-center justify-center text-white mx-auto shadow-xl shadow-brand-500/25">
            <Compass className="w-7 h-7" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
          </h1>
          <p className="text-sm text-slate-400">
            {mode === 'login'
              ? 'Sign in to track your items, view matches & verify ownership'
              : 'Join the intelligent campus lost and found network'}
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-800">
          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={form.name}
                    onChange={handleChange('name')}
                    placeholder="Alex Chen"
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-sm"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Campus Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={form.email}
                  onChange={handleChange('email')}
                  placeholder="student@campus.edu"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={form.password}
                  onChange={handleChange('password')}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-sm"
                />
              </div>
            </div>

            {err && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium">
                {err}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-blue-600 hover:from-brand-500 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-brand-600/30 transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Toggle */}
          <div className="mt-5 pt-4 border-t border-slate-800 text-center">
            <button
              type="button"
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setErr(''); }}
              className="text-xs text-slate-400 hover:text-brand-400 transition-colors"
            >
              {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
            </button>
          </div>

          {/* Quick Demo Logins */}
          <div className="mt-6 pt-5 border-t border-slate-800 space-y-2">
            <div className="text-[11px] font-mono text-slate-500 uppercase tracking-wider text-center">
              One-Click Demo Credentials
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <button
                type="button"
                onClick={() => quickLogin('admin@demo.test', 'admin12345')}
                className="p-2.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
              >
                <ShieldCheck className="w-3.5 h-3.5" /> Moderator
              </button>
              <button
                type="button"
                onClick={() => quickLogin('u0557@demo.test', 'demo1234')}
                className="p-2.5 rounded-xl bg-brand-500/10 hover:bg-brand-500/20 border border-brand-500/30 text-brand-300 text-xs font-medium flex items-center justify-center gap-1.5 transition-all"
              >
                <Sparkles className="w-3.5 h-3.5" /> Student Demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
