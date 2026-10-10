import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FilePlus, ShieldCheck, MapPin, Calendar, Clock, AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';
import api, { errMsg } from '../api';
import CampusMapPicker from '../components/CampusMapPicker';
import ImageUploader from '../components/ImageUploader';

export default function ReportForm() {
  const { type } = useParams(); // 'lost' or 'found'
  const nav = useNavigate();

  const [places, setPlaces] = useState([]);
  const [cats, setCats] = useState({});
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  const [form, setForm] = useState({
    category: '',
    brand: '',
    color: '',
    description: '',
    place_id: '',
    event_time: new Date().toISOString().slice(0, 16),
    time_window_hours: 1.0,
    handover_instructions: '',
  });

  const [hiddenDetails, setHiddenDetails] = useState({});
  const [image, setImage] = useState(null);

  useEffect(() => {
    api.get('/places').then((res) => {
      setPlaces(res.data);
      if (res.data.length > 0 && !form.place_id) {
        setForm(f => ({ ...f, place_id: String(res.data[0].id) }));
      }
    });
    api.get('/reports/categories').then((res) => setCats(res.data));
  }, []);

  const handleChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const activeQuestions = cats[form.category]?.questions || {};

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr('');
    setLoading(true);

    const fd = new FormData();
    fd.append('type', type);
    fd.append('category', form.category);
    fd.append('brand', form.brand);
    fd.append('color', form.color);
    fd.append('description', form.description);
    fd.append('place_id', form.place_id);
    fd.append('event_time', form.event_time);
    fd.append('time_window_hours', form.time_window_hours);
    
    if (!isLost && form.handover_instructions) {
      fd.append('handover_instructions', form.handover_instructions);
    }

    if (type === 'found') {
      const answersGiven = Object.values(hiddenDetails).filter(v => String(v).trim().length > 0);
      if (answersGiven.length < 3) {
        setErr('For found items, please provide answers to at least 3 private questions to protect the real owner.');
        setLoading(false);
        return;
      }
      fd.append('hidden_details', JSON.stringify(hiddenDetails));
    }

    if (image) {
      fd.append('image', image);
    }

    try {
      const res = await api.post('/reports', fd);
      nav(`/reports/${res.data.id}`);
    } catch (ex) {
      setErr(errMsg(ex, 'Could not submit report. Please check all fields.'));
    } finally {
      setLoading(false);
    }
  };

  const isLost = type === 'lost';

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Title */}
      <div className="space-y-1">
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
          isLost ? 'bg-rose-500/10 border border-rose-500/30 text-rose-300' : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isLost ? 'bg-rose-500' : 'bg-emerald-500'}`} />
          {isLost ? 'Report Missing Item' : 'Report Discovered Item'}
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
          {isLost ? 'Report a Lost Item' : 'Report a Found Item'}
        </h1>
        <p className="text-slate-400 text-sm">
          {isLost
            ? 'Describe what you lost. Our AI engine will continuously scan found records for matches.'
            : 'Help return this item to its rightful owner. Private verification questions will safeguard the release.'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-2xl space-y-6">
        {/* Category & Attributes */}
        <div className="space-y-4">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Item Details</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="sm:col-span-1 space-y-1.5">
              <label className="block text-xs font-semibold text-slate-400">Category *</label>
              <select
                required
                value={form.category}
                onChange={handleChange('category')}
                className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
              >
                <option value="">Select Category</option>
                {Object.keys(cats).map((c) => (
                  <option key={c} value={c} className="bg-slate-900">{c}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-400">Brand / Maker</label>
              <input
                type="text"
                value={form.brand}
                onChange={handleChange('brand')}
                placeholder="e.g. Nike, Apple, Milton"
                className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500 placeholder-slate-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-400">Main Colour *</label>
              <input
                type="text"
                required
                value={form.color}
                onChange={handleChange('color')}
                placeholder="e.g. Navy Blue, Black, Red"
                className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500 placeholder-slate-500"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-400">Public Description *</label>
            <textarea
              required
              rows={3}
              value={form.description}
              onChange={handleChange('description')}
              placeholder={
                isLost
                  ? "Describe visible features, stickers, wear marks or when you noticed it gone..."
                  : "Describe general appearance and where you spotted it (DO NOT include secret contents)..."
              }
              className="w-full p-3 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500 placeholder-slate-500 resize-none"
            />
          </div>
        </div>

        {/* Location & Time Picker */}
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Campus Location & Time</h2>

          <CampusMapPicker
            places={places}
            selectedId={form.place_id}
            onSelect={(id) => setForm(f => ({ ...f, place_id: String(id) }))}
          />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-400">Select Place *</label>
              <select
                required
                value={form.place_id}
                onChange={handleChange('place_id')}
                className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
              >
                {places.map((p) => (
                  <option key={p.id} value={p.id} className="bg-slate-900">{p.name}</option>
                ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-400">Approximate Time *</label>
              <input
                type="datetime-local"
                required
                value={form.event_time}
                onChange={handleChange('event_time')}
                className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
              />
            </div>

            {isLost && (
              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-400">Time Uncertainty</label>
                <select
                  value={form.time_window_hours}
                  onChange={handleChange('time_window_hours')}
                  className="w-full p-2.5 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
                >
                  <option value={0.5}>Within 30 minutes</option>
                  <option value={1.0}>Within 1 hour</option>
                  <option value={2.0}>Within 2 hours</option>
                  <option value={4.0}>Within 4 hours</option>
                  <option value={8.0}>Within half a day</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Photo Uploader */}
        <div className="pt-4 border-t border-slate-800">
          <ImageUploader file={image} onChange={setImage} label="Item Photo (Stripped of EXIF, Faces Blurred)" />
        </div>

        {/* Private Hidden Details (Found Reports Only) */}
        {!isLost && form.category && Object.keys(activeQuestions).length > 0 && (
          <div className="pt-4 border-t border-slate-800 space-y-3">
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-2">
              <div className="flex items-center gap-2 text-amber-300 font-bold text-sm">
                <ShieldCheck className="w-5 h-5 text-amber-400" /> Private Ownership Challenge Questions
              </div>
              <p className="text-xs text-amber-200/80 leading-relaxed">
                Answer at least 3 private questions below. These details are Fernet-encrypted and never shown publicly.
                Only a claimant who provides matching answers can claim this item.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 pt-2">
              {Object.entries(activeQuestions).map(([key, qText]) => (
                <div key={key} className="space-y-1">
                  <label className="block text-xs font-medium text-slate-300">{qText}</label>
                  <input
                    type="text"
                    value={hiddenDetails[key] || ''}
                    onChange={(e) => setHiddenDetails({ ...hiddenDetails, [key]: e.target.value })}
                    placeholder="Enter private detail as seen on the item..."
                    className="w-full p-2.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {!isLost && (
          <div className="pt-4 border-t border-slate-800 space-y-3">
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider">Handover / Meeting Details (Optional)</h2>
            <p className="text-xs text-slate-400">
              Where should the owner meet you or collect the item if they pass verification? (e.g. "Leave it at Admin Office", "Meet at Canteen between 1PM-2PM")
            </p>
            <textarea
              rows={2}
              value={form.handover_instructions}
              onChange={handleChange('handover_instructions')}
              placeholder="Enter meeting instructions..."
              className="w-full p-3 bg-slate-900 border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-brand-500 resize-none"
            />
          </div>
        )}

        {err && (
          <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium">
            {err}
          </div>
        )}

        {/* Submit */}
        <div className="pt-4 border-t border-slate-800 flex justify-end">
          <button
            type="submit"
            disabled={loading}
            className={`px-8 py-3 rounded-xl font-bold text-sm shadow-xl transition-all hover:scale-[1.02] flex items-center gap-2 ${
              isLost
                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-600/30'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/30'
            } disabled:opacity-50`}
          >
            {loading ? 'Processing & Matching...' : isLost ? 'Publish Lost Report' : 'Register Found Item'}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
