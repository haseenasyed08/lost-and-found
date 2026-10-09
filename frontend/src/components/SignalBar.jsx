import React from 'react';

const LABELS = {
  text: 'Text Description',
  image: 'Visual / CLIP Photo',
  color: 'Colour Match',
  brand: 'Brand Match',
  geo: 'Campus Proximity',
  time: 'Time Window Decay',
  ocr: 'OCR Text on Item',
};

const COLOR_TIERS = [
  { min: 0.8, color: 'bg-emerald-500', text: 'text-emerald-400' },
  { min: 0.5, color: 'bg-brand-500', text: 'text-brand-400' },
  { min: 0.25, color: 'bg-amber-500', text: 'text-amber-400' },
  { min: 0, color: 'bg-slate-500', text: 'text-slate-400' },
];

export default function SignalBar({ signalKey, value }) {
  if (value === null || value === undefined) return null;
  const clamped = Math.max(0, Math.min(1, value));
  const pct = Math.round(clamped * 100);
  
  const tier = COLOR_TIERS.find(t => clamped >= t.min) || COLOR_TIERS[3];

  return (
    <div className="flex items-center gap-3 text-xs py-1">
      <span className="w-32 text-slate-400 font-medium truncate">{LABELS[signalKey] || signalKey}</span>
      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/50">
        <div
          className={`h-full ${tier.color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`w-10 text-right font-mono font-semibold ${tier.text}`}>{pct}%</span>
    </div>
  );
}
