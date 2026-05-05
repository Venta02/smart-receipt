const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type TextBlock = {
  text: string;
  confidence: number;
  bbox: number[][];
};

export type ReceiptItem = {
  name: string;
  quantity: number | null;
  unit_price: number | null;
  total_price: number | null;
};

export type ExtractedFields = {
  merchant_name: string | null;
  merchant_address: string | null;
  receipt_date: string | null;
  receipt_number: string | null;
  items: ReceiptItem[];
  subtotal: number | null;
  tax: number | null;
  total: number | null;
  currency: string | null;
  payment_method: string | null;
};

export type ValidationResult = {
  passed: boolean;
  issues: string[];
  warnings: string[];
};

export type ExtractionMethod = "rule_based" | "llm_fallback" | "hybrid";

export type ExtractionResponse = {
  request_id: string;
  status: "success" | "partial" | "failed";
  document_type: string;
  language: string;
  confidence: number;
  fields: ExtractedFields;
  raw_text_blocks: TextBlock[];
  validation: ValidationResult;
  category: string | null;
  latency_ms: number;
  extraction_method: ExtractionMethod;
  metadata: Record<string, unknown>;
};

export type HealthResponse = {
  status: "ok" | "degraded" | "unhealthy";
  version: string;
  ocr_ready: boolean;
  redis_reachable: boolean;
  llm_available: boolean;
};

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function extractReceipt(
  file: File,
  deskew = true
): Promise<ExtractionResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(
    `${API_URL}/receipts/extract?deskew=${deskew}`,
    { method: "POST", body: formData }
  );
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Extraction failed: ${res.status} ${errorBody}`);
  }
  return res.json();
}