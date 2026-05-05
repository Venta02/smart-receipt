"use client";

import { useState } from "react";
import { ExtractionResponse, ExtractionMethod } from "@/lib/api";

type Props = {
  result: ExtractionResponse;
};

function formatCurrency(value: number | null, currency: string | null): string {
  if (value === null) return "—";
  const code = currency || "";
  return `${code} ${value.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`.trim();
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/30",
    partial: "bg-amber-500/10 text-amber-400 ring-amber-500/30",
    failed: "bg-red-500/10 text-red-400 ring-red-500/30",
  };
  const dots: Record<string, string> = {
    success: "bg-emerald-500",
    partial: "bg-amber-500",
    failed: "bg-red-500",
  };
  const cls = colors[status] || colors.failed;
  const dot = dots[status] || dots.failed;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {status}
    </span>
  );
}

function MethodBadge({ method }: { method: ExtractionMethod }) {
  const config: Record<ExtractionMethod, { label: string; cls: string; tooltip: string }> = {
    rule_based: {
      label: "Rule-based",
      cls: "bg-blue-500/10 text-blue-400 ring-blue-500/30",
      tooltip: "Extracted using regex patterns and spatial heuristics. Fast and free.",
    },
    llm_fallback: {
      label: "Gemini",
      cls: "bg-purple-500/10 text-purple-400 ring-purple-500/30",
      tooltip: "Extracted using Gemini Vision API. Higher accuracy for complex layouts.",
    },
    hybrid: {
      label: "Hybrid",
      cls: "bg-fuchsia-500/10 text-fuchsia-400 ring-fuchsia-500/30",
      tooltip: "Combined rule-based and LLM signals. Best of both.",
    },
  };
  const c = config[method];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${c.cls}`}
      title={c.tooltip}
    >
      {c.label}
    </span>
  );
}

function CategoryBadge({ category }: { category: string | null }) {
  if (!category) return null;
  const config: Record<string, { label: string; emoji: string }> = {
    food: { label: "Food", emoji: "🍔" },
    transportation: { label: "Transport", emoji: "🚗" },
    shopping: { label: "Shopping", emoji: "🛍️" },
    healthcare: { label: "Healthcare", emoji: "🏥" },
    entertainment: { label: "Entertainment", emoji: "🎬" },
    utilities: { label: "Utilities", emoji: "💡" },
    other: { label: "Other", emoji: "📄" },
  };
  const c = config[category] || config.other;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800/80 px-2.5 py-1 text-xs font-medium text-zinc-300 ring-1 ring-zinc-700">
      <span className="text-sm">{c.emoji}</span>
      <span>{c.label}</span>
    </span>
  );
}

export default function ResultPanel({ result }: Props) {
  const { fields, validation, category } = result;
  const [showCoords, setShowCoords] = useState(false);
  const [copyStatus, setCopyStatus] = useState<string | null>(null);
  const [expandRaw, setExpandRaw] = useState(false);

  const copyAllOcr = async () => {
    const text = result.raw_text_blocks
      .map((b, i) =>
        `${i + 1}. [${(b.confidence * 100).toFixed(0)}%] ${b.text}${
          showCoords && b.bbox ? ` @ (${Math.round(b.bbox[0][0])},${Math.round(b.bbox[0][1])})` : ""
        }`
      )
      .join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("Copied");
      setTimeout(() => setCopyStatus(null), 2000);
    } catch {
      setCopyStatus("Failed");
      setTimeout(() => setCopyStatus(null), 2000);
    }
  };

  return (
    <div className="space-y-4">
      {/* Status bar */}
      <div className="rounded-xl bg-zinc-900/40 ring-1 ring-zinc-800 px-5 py-3 flex flex-wrap items-center gap-3">
        <StatusBadge status={result.status} />
        <MethodBadge method={result.extraction_method} />
        <CategoryBadge category={category} />
        <div className="ml-auto flex items-center gap-3 text-xs font-mono text-zinc-500">
          <span>{result.document_type}</span>
          <span className="text-zinc-700">·</span>
          <span>{(result.latency_ms / 1000).toFixed(2)}s</span>
        </div>
      </div>

      {/* LLM fallback notice */}
      {result.metadata?.fallback_reason && (
        <div className="rounded-xl bg-purple-950/20 ring-1 ring-purple-900/40 px-5 py-3 flex items-start gap-3">
          <div className="h-5 w-5 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
            <span className="text-[10px]">🤖</span>
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-purple-300 mb-0.5">Gemini Vision used</p>
            <p className="text-xs text-purple-200/60 leading-relaxed">
              {String(result.metadata.fallback_reason)}
            </p>
          </div>
        </div>
      )}

      {/* Validation issues/warnings */}
      {validation.issues.length > 0 && (
        <div className="rounded-xl bg-red-950/20 ring-1 ring-red-900/40 px-5 py-3">
          <p className="text-xs font-medium text-red-300 mb-2">Issues</p>
          <ul className="space-y-1 text-xs text-red-200/70 leading-relaxed">
            {validation.issues.map((issue, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-red-500 flex-shrink-0">•</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {validation.warnings.length > 0 && (
        <div className="rounded-xl bg-amber-950/20 ring-1 ring-amber-900/40 px-5 py-3">
          <p className="text-xs font-medium text-amber-300 mb-2">Warnings</p>
          <ul className="space-y-1 text-xs text-amber-200/70 leading-relaxed">
            {validation.warnings.map((warning, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-amber-500 flex-shrink-0">•</span>
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Merchant card */}
      <div className="rounded-xl bg-zinc-900/40 ring-1 ring-zinc-800 overflow-hidden">
        <div className="px-5 py-2.5 border-b border-zinc-800/60 flex items-center justify-between">
          <h3 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Merchant
          </h3>
        </div>
        <div className="px-5 py-4">
          <p className="text-lg font-medium text-white mb-3 leading-tight">
            {fields.merchant_name || <span className="text-zinc-600">Unknown merchant</span>}
          </p>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            <Field label="Date" value={fields.receipt_date} mono />
            <Field label="Receipt no." value={fields.receipt_number} mono />
            <Field label="Payment" value={fields.payment_method} />
            <Field label="Currency" value={fields.currency} mono />
          </div>
        </div>
      </div>

      {/* Items table */}
      {fields.items.length > 0 && (
        <div className="rounded-xl bg-zinc-900/40 ring-1 ring-zinc-800 overflow-hidden">
          <div className="px-5 py-2.5 border-b border-zinc-800/60 flex items-center justify-between">
            <h3 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              Items
            </h3>
            <span className="text-xs text-zinc-600 font-mono">
              {fields.items.length}
            </span>
          </div>
          <div className="overflow-hidden">
            <table className="w-full text-sm">
              <thead className="text-xs text-zinc-600">
                <tr className="border-b border-zinc-800/60">
                  <th className="px-5 py-2 text-left font-medium">Item</th>
                  <th className="px-5 py-2 text-right font-medium w-16">Qty</th>
                  <th className="px-5 py-2 text-right font-medium w-32">Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {fields.items.map((item, i) => (
                  <tr key={i} className="hover:bg-zinc-800/20 transition">
                    <td className="px-5 py-2.5 text-zinc-200 leading-snug">
                      {item.name}
                    </td>
                    <td className="px-5 py-2.5 text-right text-zinc-500 font-mono text-xs">
                      {item.quantity ?? "—"}
                    </td>
                    <td className="px-5 py-2.5 text-right text-zinc-200 font-mono text-xs whitespace-nowrap">
                      {formatCurrency(item.total_price, fields.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Totals card */}
      <div className="rounded-xl bg-zinc-900/40 ring-1 ring-zinc-800 overflow-hidden">
        <div className="px-5 py-2.5 border-b border-zinc-800/60">
          <h3 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
            Totals
          </h3>
        </div>
        <div className="px-5 py-4 space-y-2.5">
          <TotalRow label="Subtotal" value={fields.subtotal} currency={fields.currency} />
          <TotalRow label="Tax" value={fields.tax} currency={fields.currency} />
          <div className="pt-2.5 mt-2.5 border-t border-zinc-800/60 flex items-center justify-between">
            <span className="text-sm font-medium text-white">Total</span>
            <span className="text-xl font-mono font-semibold text-emerald-400 whitespace-nowrap">
              {formatCurrency(fields.total, fields.currency)}
            </span>
          </div>
        </div>
      </div>

      {/* Raw OCR (collapsible) */}
      <div className="rounded-xl bg-zinc-900/40 ring-1 ring-zinc-800 overflow-hidden">
        <button
          onClick={() => setExpandRaw(!expandRaw)}
          className="w-full px-5 py-2.5 border-b border-zinc-800/60 flex items-center justify-between hover:bg-zinc-800/20 transition"
        >
          <div className="flex items-center gap-3">
            <h3 className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">
              Raw OCR
            </h3>
            <span className="text-xs text-zinc-600 font-mono">
              {result.raw_text_blocks.length} blocks
            </span>
          </div>
          <svg
            className={`h-4 w-4 text-zinc-600 transition-transform ${expandRaw ? "rotate-180" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {expandRaw && (
          <>
            <div className="px-5 py-2 border-b border-zinc-800/60 flex items-center justify-end gap-3">
              <label className="flex items-center gap-1.5 text-xs text-zinc-500 cursor-pointer hover:text-zinc-300">
                <input
                  type="checkbox"
                  checked={showCoords}
                  onChange={(e) => setShowCoords(e.target.checked)}
                  className="accent-emerald-500"
                />
                coords
              </label>
              <button
                onClick={copyAllOcr}
                className="text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded ring-1 ring-zinc-800 hover:ring-zinc-700 transition"
              >
                {copyStatus || "Copy"}
              </button>
            </div>
            <div className="px-5 py-3 max-h-[400px] overflow-y-auto">
              <table className="w-full text-xs">
                <tbody>
                  {result.raw_text_blocks.map((block, i) => (
                    <tr key={i} className="hover:bg-zinc-800/20">
                      <td className="py-1.5 pr-3 text-zinc-700 font-mono w-8">{i + 1}</td>
                      <td className="py-1.5 pr-3 text-zinc-500 font-mono w-12">
                        {(block.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="py-1.5 pr-3 text-zinc-300 font-mono break-all">
                        {block.text}
                      </td>
                      {showCoords && (
                        <td className="py-1.5 pr-3 text-zinc-600 font-mono w-32 whitespace-nowrap">
                          {block.bbox && block.bbox[0]
                            ? `(${Math.round(block.bbox[0][0])}, ${Math.round(block.bbox[0][1])})`
                            : "—"}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string | null; mono?: boolean }) {
  return (
    <div>
      <p className="text-[11px] text-zinc-500 mb-1">{label}</p>
      <p className={`text-sm text-zinc-200 ${mono ? "font-mono" : ""}`}>
        {value || <span className="text-zinc-600">—</span>}
      </p>
    </div>
  );
}

function TotalRow({ label, value, currency }: { label: string; value: number | null; currency: string | null }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-zinc-400">{label}</span>
      <span className="text-zinc-300 font-mono text-xs">
        {formatCurrency(value, currency)}
      </span>
    </div>
  );
}
