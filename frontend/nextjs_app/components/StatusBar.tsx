"use client";

import { HealthResponse } from "@/lib/api";

type Props = {
  health: HealthResponse | null;
};

export default function StatusBar({ health }: Props) {
  const isOk = health?.status === "ok";
  const dotColor = isOk
    ? "bg-emerald-500"
    : health?.status === "degraded"
    ? "bg-amber-500"
    : "bg-red-500";

  return (
    <div className="border-b border-zinc-900 bg-zinc-950/90 backdrop-blur-md sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-6 py-2.5 flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className={`h-1.5 w-1.5 rounded-full ${dotColor} ${health ? "animate-pulse" : ""}`} />
            <span className="font-medium text-zinc-300 font-mono">
              smart-receipt
            </span>
            <span className="text-zinc-700 font-mono">
              {health ? `v${health.version}` : "offline"}
            </span>
          </div>
          {health && (
            <div className="hidden md:flex items-center gap-3 pl-3 border-l border-zinc-800">
              <Service label="OCR" ready={health.ocr_ready} />
              <Service label="Redis" ready={health.redis_reachable} />
              <Service label="LLM" ready={health.llm_available} />
            </div>
          )}
        </div>
        <div className="hidden md:flex text-zinc-600 font-mono items-center gap-2">
          <span>PaddleOCR</span>
          <span className="text-zinc-800">·</span>
          <span>Gemini</span>
          <span className="text-zinc-800">·</span>
          <span>FastAPI</span>
        </div>
      </div>
    </div>
  );
}

function Service({ label, ready }: { label: string; ready: boolean }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-zinc-500 font-mono">{label}</span>
      <span
        className={`text-[10px] font-mono ${
          ready ? "text-emerald-400" : "text-zinc-600"
        }`}
      >
        {ready ? "●" : "○"}
      </span>
    </div>
  );
}
