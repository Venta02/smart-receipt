"use client";

import { useEffect, useState } from "react";
import StatusBar from "@/components/StatusBar";
import UploadZone from "@/components/UploadZone";
import ResultPanel from "@/components/ResultPanel";
import {
  checkHealth,
  extractReceipt,
  ExtractionResponse,
  HealthResponse,
} from "@/lib/api";

export default function Home() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [result, setResult] = useState<ExtractionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = () => {
      checkHealth().then(setHealth).catch(() => setHealth(null));
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFile = async (file: File) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setPreviewUrl(URL.createObjectURL(file));
    try {
      const data = await extractReceipt(file, true);
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setPreviewUrl(null);
    setError(null);
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      <StatusBar health={health} />

      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-3">
            <div className="h-1 w-8 bg-gradient-to-r from-emerald-500 to-purple-500 rounded-full" />
            <span className="text-xs uppercase tracking-widest text-zinc-500 font-medium">
              Receipt Intelligence
            </span>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight mb-4 bg-gradient-to-br from-white via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            smart-receipt
          </h1>
          <p className="text-lg text-zinc-400 max-w-2xl leading-relaxed">
            Hybrid OCR pipeline with rule-based extraction and Gemini Vision fallback.
            Production-grade receipt understanding for fintech and accounting workflows.
          </p>
        </div>

        {/* Two column layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-8">
          {/* Left column: Upload + Preview (sticky) */}
          <div className="lg:sticky lg:top-20 lg:self-start space-y-4">
            <UploadZone
              onFileSelect={handleFile}
              loading={loading}
              previewUrl={previewUrl}
              onReset={handleReset}
            />

            {/* Quick stats card */}
            {result && (
              <div className="rounded-xl bg-zinc-900/50 ring-1 ring-zinc-800 p-4 space-y-3">
                <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  Pipeline Metrics
                </h3>
                <div className="grid grid-cols-2 gap-3">
                  <Stat
                    label="Latency"
                    value={`${(result.latency_ms / 1000).toFixed(1)}s`}
                  />
                  <Stat
                    label="OCR Conf"
                    value={`${(result.confidence * 100).toFixed(0)}%`}
                  />
                  <Stat
                    label="OCR Blocks"
                    value={`${result.raw_text_blocks.length}`}
                  />
                  <Stat
                    label="Items"
                    value={`${result.fields.items.length}`}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Right column: Results */}
          <div>
            {error && (
              <div className="rounded-xl bg-red-950/30 ring-1 ring-red-900/40 px-5 py-4 mb-6">
                <p className="text-sm font-medium text-red-300 mb-1">Extraction failed</p>
                <p className="text-xs text-red-200/70 font-mono">{error}</p>
              </div>
            )}

            {loading && <LoadingState />}

            {result && !loading && <ResultPanel result={result} />}

            {!result && !loading && !error && <EmptyState llmEnabled={health?.llm_available || false} />}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-zinc-900/60 mt-20 py-6 text-center text-xs text-zinc-600">
        Built with PaddleOCR · FastAPI · Next.js · Gemini Vision
      </footer>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-zinc-600 mb-0.5">{label}</p>
      <p className="text-sm font-mono font-medium text-zinc-200">{value}</p>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="rounded-2xl bg-zinc-900/40 ring-1 ring-zinc-800 p-12">
      <div className="flex flex-col items-center text-center max-w-md mx-auto">
        <div className="relative mb-6">
          <div className="h-16 w-16 rounded-full border-2 border-zinc-800 border-t-emerald-500 animate-spin" />
          <div className="absolute inset-0 h-16 w-16 rounded-full border-2 border-transparent border-r-purple-500 animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
        </div>
        <h3 className="text-base font-medium text-white mb-2">Processing receipt</h3>
        <p className="text-sm text-zinc-500 mb-6 leading-relaxed">
          Running OCR pipeline. If rule-based confidence is low, will fallback to Gemini Vision.
        </p>
        <div className="w-full space-y-2">
          <PipelineStep label="Image quality validation" active={false} done={true} />
          <PipelineStep label="OCR text detection (PaddleOCR)" active={true} done={false} />
          <PipelineStep label="Field extraction" active={false} done={false} />
          <PipelineStep label="LLM fallback (if needed)" active={false} done={false} />
        </div>
      </div>
    </div>
  );
}

function PipelineStep({ label, active, done }: { label: string; active: boolean; done: boolean }) {
  return (
    <div className="flex items-center gap-3 text-left text-xs">
      <div
        className={`h-1.5 w-1.5 rounded-full ${
          done ? "bg-emerald-500" : active ? "bg-emerald-400 animate-pulse" : "bg-zinc-700"
        }`}
      />
      <span className={done || active ? "text-zinc-300" : "text-zinc-600"}>
        {label}
      </span>
    </div>
  );
}

function EmptyState({ llmEnabled }: { llmEnabled: boolean }) {
  return (
    <div className="rounded-2xl bg-zinc-900/40 ring-1 ring-zinc-800 p-12">
      <div className="max-w-lg mx-auto">
        <div className="mb-6">
          <div className="h-12 w-12 rounded-xl bg-zinc-800/50 ring-1 ring-zinc-800 flex items-center justify-center mb-4">
            <svg className="h-6 w-6 text-zinc-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-base font-medium text-white mb-2">Upload a receipt to begin</h3>
          <p className="text-sm text-zinc-500 leading-relaxed">
            Drop or click the upload zone on the left. The pipeline will detect text,
            extract structured fields, and categorize the receipt.
          </p>
        </div>

        <div className="space-y-3">
          <h4 className="text-xs uppercase tracking-wider text-zinc-600 font-medium">
            How it works
          </h4>
          <div className="space-y-2.5">
            <Step number={1} title="Image validation" desc="Reject blurry or low-resolution input early" />
            <Step number={2} title="PaddleOCR detection" desc="Extract text blocks with bounding box coordinates" />
            <Step number={3} title="Rule-based extraction" desc="Spatial pattern matching for merchant, date, items, totals" />
            <Step number={4} title={llmEnabled ? "Gemini Vision fallback" : "LLM fallback (disabled)"} desc={llmEnabled ? "Triggered when rule-based confidence is below threshold" : "Set GEMINI_API_KEY in .env to enable"} muted={!llmEnabled} />
            <Step number={5} title="Validation & categorization" desc="Cross-check totals, classify into 7 spending categories" />
          </div>
        </div>
      </div>
    </div>
  );
}

function Step({ number, title, desc, muted = false }: { number: number; title: string; desc: string; muted?: boolean }) {
  return (
    <div className={`flex items-start gap-3 ${muted ? "opacity-50" : ""}`}>
      <div className="h-5 w-5 rounded-full bg-zinc-800 ring-1 ring-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-[10px] font-mono text-zinc-400">{number}</span>
      </div>
      <div className="min-w-0">
        <p className="text-sm text-zinc-300 font-medium leading-snug">{title}</p>
        <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
