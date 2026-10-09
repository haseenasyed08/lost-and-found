import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Search, Image as ImageIcon, MapPin, Calendar, Sparkles, Filter, CheckCircle2, ArrowRight } from 'lucide-react';
import api, { getImageUrl, errMsg } from '../api';
import ImageUploader from '../components/ImageUploader';

export default function Home() {
  const [text, setText] = useState('');
  const [category, setCategory] = useState('');
  const [image, setImage] = useState(null);
  const [categories, setCategories] = useState({});
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    api.get('/reports/categories')
      .then(res => setCategories(res.data))
      .catch(() => {});
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!text.trim() && !image) {
      setErr('Please provide a description keyword, an image, or both.');
      return;
    }
    setErr('');
    setLoading(true);
    const fd = new FormData();
    if (text.trim()) fd.append('text', text.trim());
    if (category) fd.append('category', category);
    if (image) fd.append('image', image);

    try {
      const res = await api.post('/search', fd);
      setResults(res.data);
    } catch (ex) {
      setErr(errMsg(ex, 'Multimodal search failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero Header */}
      <div className="relative rounded-3xl p-8 sm:p-12 overflow-hidden border border-slate-800 glass-panel">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-brand-400" /> Multimodal CLIP & Paraphrase-MiniLM Embeddings
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Lost Something? <br />
            <span className="bg-gradient-to-r from-brand-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
              Search by Text, Photo, or Both.
            </span>
          </h1>
          <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
            Our multi-factor matching engine computes semantic text similarity, cross-modal image alignments,
            campus location decay, and dominant attributes to suggest true matches.
          </p>
        </div>

        {/* Quick Report CTAs */}
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/report/lost"
            className="px-5 py-2.5 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white font-semibold text-sm shadow-lg shadow-rose-600/20 transition-all flex items-center gap-2"
          >
            I Lost an Item <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            to="/report/found"
            className="px-5 py-2.5 rounded-xl bg-emerald-600/90 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2"
          >
            I Found an Item <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Multimodal Search Card */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-xl space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-brand-400" /> Search Open Found Items
          </h2>
          <span className="text-xs text-slate-400 font-mono">Neural Cross-Modal Retrieval</span>
        </div>

        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Text description search */}
            <div className="md:col-span-2 space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Item Description or Keywords
              </label>
              <textarea
                rows={2}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="e.g. Navy blue Wildcraft backpack with white logo, or Casio scientific calculator..."
                className="w-full p-3 bg-slate-900/80 border border-slate-700/80 rounded-2xl text-white placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-sm resize-none"
              />
            </div>

            {/* Category filter */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Category Filter (Optional)
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-3 bg-slate-900/80 border border-slate-700/80 rounded-2xl text-white focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 text-sm"
              >
                <option value="">All Categories</option>
                {Object.keys(categories).map((c) => (
                  <option key={c} value={c} className="bg-slate-900">{c}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Image Uploader */}
          <div className="pt-2">
            <ImageUploader
              file={image}
              onChange={setImage}
              label="Query Photo (Search by reference picture)"
            />
          </div>

          {err && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-medium">
              {err}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-semibold text-sm shadow-lg shadow-brand-600/30 transition-all hover:scale-[1.02] flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? 'Analyzing Vectors...' : 'Search Matching Items'}
              <Search className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Search Results Display */}
      {results !== null && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">
              Search Results ({results.length})
            </h3>
            <span className="text-xs text-slate-400">Ranked by Cosine Similarity</span>
          </div>

          {results.length === 0 ? (
            <div className="glass-panel rounded-2xl p-8 text-center text-slate-400 border border-slate-800">
              No matching found items found. Try broadening your keywords or removing the category filter.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.map((item) => (
                <div
                  key={item.id}
                  className="glass-panel rounded-2xl p-5 border border-slate-800 hover:border-brand-500/40 transition-all hover:-translate-y-1 shadow-lg space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    {/* Header tags */}
                    <div className="flex items-center justify-between">
                      <span className="px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-300 border border-slate-700">
                        {item.category}
                      </span>
                      <span className="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                        {Math.round(item.score * 100)}% Match
                      </span>
                    </div>

                    {/* Image thumbnail if present */}
                    {item.images && item.images[0] && (
                      <div className="relative h-40 w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                        <img
                          src={getImageUrl(item.images[0])}
                          alt={item.description}
                          className="w-full h-full object-cover"
                        />
                        <span className="absolute bottom-1 right-2 text-[10px] font-mono bg-black/60 px-1.5 py-0.5 rounded text-slate-300">
                          Blurred Public Photo
                        </span>
                      </div>
                    )}

                    <div>
                      <h4 className="font-semibold text-white capitalize text-base">
                        {item.color} {item.brand} {item.category}
                      </h4>
                      <p className="text-xs text-slate-300 line-clamp-2 mt-1 leading-relaxed">
                        {item.description}
                      </p>
                    </div>

                    <div className="text-xs text-slate-400 space-y-1 pt-2 border-t border-slate-800/80">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-brand-400" />
                        <span>{item.place}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-500" />
                        <span>{new Date(item.event_time).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>

                  <Link
                    to={`/reports/${item.id}`}
                    className="w-full py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold text-center transition-colors block"
                  >
                    View Details
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
