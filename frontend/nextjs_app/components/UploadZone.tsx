"use client";

import { useRef, useState, ChangeEvent, DragEvent } from "react";

type Props = {
  onFileSelect: (file: File) => void;
  loading: boolean;
  previewUrl: string | null;
  onReset: () => void;
};

export default function UploadZone({ onFileSelect, loading, previewUrl, onReset }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFile = (file: File) => {
    if (!file.type.startsWith("image/")) return;
    onFileSelect(file);
  };

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  if (previewUrl) {
    return (
      <div className="rounded-xl bg-zinc-900/50 ring-1 ring-zinc-800 overflow-hidden">
        <div className="relative aspect-[3/4] bg-black/50">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Receipt"
            className="absolute inset-0 w-full h-full object-contain"
          />
          {loading && (
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center backdrop-blur-sm">
              <div className="bg-zinc-900/90 rounded-full px-4 py-2 ring-1 ring-zinc-700 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-xs font-medium text-white">Processing</span>
              </div>
            </div>
          )}
        </div>
        <div className="px-4 py-3 flex items-center justify-between gap-2 border-t border-zinc-800">
          <button
            onClick={() => inputRef.current?.click()}
            disabled={loading}
            className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 rounded-md ring-1 ring-zinc-800 hover:ring-zinc-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Change image
          </button>
          <button
            onClick={onReset}
            disabled={loading}
            className="text-xs text-zinc-500 hover:text-zinc-300 px-3 py-1.5 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset
          </button>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={onChange}
          className="hidden"
          disabled={loading}
        />
      </div>
    );
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
      onDragLeave={() => setDragActive(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={`relative cursor-pointer rounded-xl border-2 border-dashed transition-all ${
        dragActive
          ? "border-emerald-500/50 bg-emerald-500/5"
          : "border-zinc-800 bg-zinc-900/30 hover:border-zinc-700 hover:bg-zinc-900/50"
      } ${loading ? "pointer-events-none opacity-60" : ""}`}
    >
      <div className="px-6 py-12 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-zinc-800/60 ring-1 ring-zinc-800">
          <svg className="h-5 w-5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <p className="text-sm text-zinc-200 font-medium mb-1">Upload receipt image</p>
        <p className="text-xs text-zinc-500">Drop here or click to browse</p>
        <p className="text-xs text-zinc-600 mt-3 font-mono">PNG · JPG · WEBP · max 10MB</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={onChange}
        className="hidden"
        disabled={loading}
      />
    </div>
  );
}
