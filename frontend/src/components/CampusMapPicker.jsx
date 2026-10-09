import React from 'react';
import { MapPin, CheckCircle2 } from 'lucide-react';

export default function CampusMapPicker({ places, selectedId, onSelect }) {
  // Compute dynamic bounding box for campus map display based on places
  const lats = places.map(p => p.latitude);
  const lons = places.map(p => p.longitude);
  
  // Provide defaults if no places, otherwise add a 10% padding
  const minLatRaw = lats.length ? Math.min(...lats) : 12.8970;
  const maxLatRaw = lats.length ? Math.max(...lats) : 12.9030;
  const minLonRaw = lons.length ? Math.min(...lons) : 77.4970;
  const maxLonRaw = lons.length ? Math.max(...lons) : 77.5040;

  // Add slight padding so pins don't touch edges
  const latPad = Math.max(0.001, (maxLatRaw - minLatRaw) * 0.1);
  const lonPad = Math.max(0.001, (maxLonRaw - minLonRaw) * 0.1);

  const minLat = minLatRaw - latPad;
  const maxLat = maxLatRaw + latPad;
  const minLon = minLonRaw - lonPad;
  const maxLon = maxLonRaw + lonPad;

  const getPos = (p) => {
    const x = ((p.longitude - minLon) / (maxLon - minLon)) * 100;
    // Invert Y because latitude goes up northwards
    const y = 100 - ((p.latitude - minLat) / (maxLat - minLat)) * 100;
    return {
      left: `${Math.max(4, Math.min(96, x))}%`,
      top: `${Math.max(4, Math.min(96, y))}%`
    };
  };

  const selectedPlace = places.find(p => p.id === Number(selectedId));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1.5 font-medium text-slate-300">
          <MapPin className="w-3.5 h-3.5 text-brand-400" /> Interactive Campus Layout
        </span>
        {selectedPlace && (
          <span className="text-emerald-400 flex items-center gap-1 font-mono">
            <CheckCircle2 className="w-3 h-3" /> Selected: {selectedPlace.name}
          </span>
        )}
      </div>

      <div className="relative w-full h-64 bg-slate-950/70 border border-slate-800 rounded-2xl overflow-hidden shadow-inner p-2 select-none group">
        {/* Grid and walkway paths */}
        <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] opacity-40" />
        
        {/* Simulated campus perimeter / zones */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-dashed border-slate-700/40 rounded-full pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-72 h-72 border border-dashed border-slate-800/40 rounded-full pointer-events-none" />

        {/* Place Markers */}
        {places.map((p) => {
          const isSelected = Number(selectedId) === p.id;
          const pos = getPos(p);

          return (
            <button
              type="button"
              key={p.id}
              onClick={() => onSelect(p.id)}
              style={pos}
              className={`absolute -translate-x-1/2 -translate-y-1/2 z-10 flex flex-col items-center group/pin transition-all duration-200 ${
                isSelected ? 'scale-110 z-20' : 'hover:scale-105'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold shadow-md transition-all ${
                  isSelected
                    ? 'bg-brand-500 text-white ring-4 ring-brand-500/30 glow-blue animate-bounce-short'
                    : 'bg-slate-800/90 text-slate-300 border border-slate-700 group-hover/pin:bg-slate-700 group-hover/pin:text-white'
                }`}
              >
                <MapPin className="w-3.5 h-3.5" />
              </div>
              <span
                className={`mt-1 text-[10px] px-1.5 py-0.5 rounded tracking-tight whitespace-nowrap transition-all ${
                  isSelected
                    ? 'bg-brand-500/90 text-white font-bold shadow'
                    : 'bg-slate-900/90 text-slate-400 group-hover/pin:text-slate-200 border border-slate-800/60'
                }`}
              >
                {p.name}
              </span>
            </button>
          );
        })}
      </div>

      <div className="text-[11px] text-slate-400 flex items-center justify-between px-1">
        <span>Click any building above or use the dropdown to set report coordinates</span>
        <span className="font-mono text-slate-400">16 Campus Zones</span>
      </div>
    </div>
  );
}
