// 集中式 API 层：页面只调用这里，不散落 fetch。
export type CredibilityLabel = "official" | "multi_source" | "early_signal";

export type EvidenceItem = {
  source_item_id: number;
  title: string;
  url: string;
  source_name: string;
  published_at: string | null;
};

export type Topic = {
  id: number;
  title: string;
  what_happened: string;
  why_now: string;
  angle: string;
  hook: string;
  structure: string;
  visual: string;
  time_window: string;
  order_index: number;
  hot_event_id: number;
  credibility_label: CredibilityLabel | null;
  event_published_at: string | null;
  evidence: EvidenceItem[];
};

export type Brief = {
  id: number;
  summary: string;
  order_index: number;
  hot_event_id: number;
  event_published_at: string | null;
};

export type Report = {
  id: number;
  report_date: string;
  status: "draft" | "published";
  summary: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  last_collect_at: string | null;
  topics: Topic[];
  briefs: Brief[];
};

const BASE = "/api/v1";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`请求失败（${res.status}）`);
  }
  return res.json();
}

export async function listReports(): Promise<Report[]> {
  return getJson<Report[]>("/reports");
}

export async function getReport(id: number): Promise<Report> {
  return getJson<Report>(`/reports/${id}`);
}
