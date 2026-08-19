// 集中式 API 层：页面只调用这里，不散落 fetch。
import { getToken } from "@/lib/auth";

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
  evidence: EvidenceItem[];
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

export type PersonalizedTopic = {
  id: number;
  title: string;
  what_happened: string;
  why_now: string;
  angle: string;
  hook: string;
  structure: string;
  visual: string;
  time_window: string;
  recommendation_reason: string;
  order_index: number;
  hot_event_id: number;
  credibility_label: CredibilityLabel | null;
  event_published_at: string | null;
  evidence: EvidenceItem[];
};

export type PersonalizedReport = {
  id: number;
  report_date: string;
  summary: string | null;
  reason: string | null;
  created_at: string;
};

export type PersonalizedReportDetail = PersonalizedReport & {
  topics: PersonalizedTopic[];
};

export type Profile = {
  positioning: string;
  audience: string;
  persona: string;
  style: string;
  video_length: string;
  forbidden: string;
  updated_at: string;
};

export type Job = {
  id: number;
  kind: string;
  status: "pending" | "running" | "success" | "failed";
  result_ref: string | null;
  error_message: string | null;
};

const BASE = "/api/v1";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers, cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `请求失败（${res.status}）`);
  }
  return res.json();
}

// ---- 公开日报 ----
export async function listReports(): Promise<Report[]> {
  return apiFetch<Report[]>("/reports");
}
export async function getReport(id: number): Promise<Report> {
  return apiFetch<Report>(`/reports/${id}`);
}

// ---- 鉴权 ----
export async function apiRegister(email: string, password: string, invite_code: string) {
  return apiFetch<{ token: string; user: { id: number; email: string } }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, invite_code }),
  });
}
export async function apiLogin(email: string, password: string) {
  return apiFetch<{ token: string; user: { id: number; email: string } }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

// ---- 画像 ----
export async function getProfile(): Promise<Profile | null> {
  return apiFetch<Profile | null>("/profile");
}
export async function saveProfile(profile: Omit<Profile, "updated_at">): Promise<Profile> {
  return apiFetch<Profile>("/profile", { method: "PUT", body: JSON.stringify(profile) });
}

// ---- 个性化日报 ----
export async function generatePersonalized(): Promise<{ job_id: number }> {
  return apiFetch<{ job_id: number }>("/personalized/generate", { method: "POST" });
}
export async function listPersonalizedReports(): Promise<PersonalizedReport[]> {
  return apiFetch<PersonalizedReport[]>("/personalized/reports");
}
export async function getPersonalizedReport(id: number): Promise<PersonalizedReportDetail> {
  return apiFetch<PersonalizedReportDetail>(`/personalized/reports/${id}`);
}

// ---- 任务 ----
export async function getJob(id: number): Promise<Job> {
  return apiFetch<Job>(`/jobs/${id}`);
}
