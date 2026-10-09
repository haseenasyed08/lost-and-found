import React, { useState, useRef } from 'react';
import { Upload, X, Image as ImageIcon, ShieldAlert } from 'lucide-react';

export default function ImageUploader({ file, onChange, label = 'Attach Photo (Optional)' }) {
  const [preview, setPreview] = useState(null);
  const inputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      onChange(selected);
      const reader = new FileReader();
      reader.onload = (ev) => setPreview(ev.target?.result);
      reader.readAsDataURL(selected);
    }
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    onChange(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">{label}</label>
      
      <div
        onClick={() => inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-2xl p-4 flex flex-col items-center justify-center cursor-pointer transition-all ${
          preview
            ? 'border-brand-500/50 bg-slate-900/60'
            : 'border-slate-700/80 hover:border-brand-500/50 bg-slate-900/30 hover:bg-slate-900/60'
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileChange}
          className="hidden"
        />

        {preview ? (
          <div className="relative w-full flex items-center justify-center py-2">
            <img
              src={preview}
              alt="Preview"
              className="max-h-48 rounded-xl object-contain shadow-md border border-slate-700"
            />
            <button
              type="button"
              onClick={handleRemove}
              className="absolute top-0 right-2 p-1.5 rounded-full bg-rose-600/90 hover:bg-rose-500 text-white shadow-lg transition-transform hover:scale-110"
              title="Remove image"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="py-4 text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center mx-auto text-slate-400 group-hover:text-brand-400 transition-colors">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                Click to upload or drag & drop photo
              </p>
              <p className="text-xs text-slate-400 mt-0.5">JPEG, PNG or WebP up to 10MB</p>
            </div>
          </div>
        )}

        <div className="mt-2 text-[11px] text-slate-400 flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-brand-400" />
          <span>Faces are automatically detected & blurred. EXIF metadata is stripped.</span>
        </div>
      </div>
    </div>
  );
}
