// 集中式 API 层：页面只调用这里，不散落 fetch。
import { getOperatorKey, getToken } from "@/lib/auth";

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
  feedback_status: "want" | "not_interested" | "published" | null;
  feedback_douyin_url: string | null;
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

export type Plan = {
  id: number;
  topic_id: number;
  core_viewpoint: string;
  hooks: string[];
  structure: string;
  visual: string;
  titles: string[];
  risks: string;
  created_at: string;
};

export type Feedback = {
  id: number;
  topic_id: number;
  status: "want" | "not_interested" | "published";
  douyin_url: string | null;
  updated_at: string;
};

export type Subscription = {
  id: number;
  price_type: "founding" | "standard";
  monthly_price: number;
  status: string;
  started_at: string;
  expires_at: string;
};

const BASE = "/api/v1";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (path.startsWith("/admin")) {
    const opKey = getOperatorKey();
    if (opKey) headers["X-Operator-Key"] = opKey;
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers, cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `请求失败（${res.status}）`);
  }
  if (res.status === 204) return undefined as T;
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

// ---- 创作方案 - 发布反馈 - 订阅 ----
export async function generatePlan(topicId: number): Promise<{ job_id: number }> {
  return apiFetch<{ job_id: number }>(`/topics/${topicId}/plan`, { method: "POST" });
}
export async function getPlan(topicId: number): Promise<Plan> {
  return apiFetch<Plan>(`/topics/${topicId}/plan`);
}
export async function submitFeedback(
  topicId: number,
  status: "want" | "not_interested" | "published",
  douyin_url?: string,
): Promise<Feedback> {
  return apiFetch<Feedback>(`/topics/${topicId}/feedback`, {
    method: "PUT",
    body: JSON.stringify({ status, douyin_url }),
  });
}
export async function getMySubscription(): Promise<Subscription | null> {
  return apiFetch<Subscription | null>("/subscriptions/me");
}

// ---- 质检（运营者，本地直调）----
export type ReviewTopic = {
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
  reviewed: boolean;
  evidence: EvidenceItem[];
};

export type CandidateEvent = {
  id: number;
  title: string;
  summary: string;
  credibility_label: CredibilityLabel;
  sort_score: number;
  evidence_count: number;
};

export type ReviewPayload = {
  report_id: number | null;
  report_date: string | null;
  status: "draft" | "published" | null;
  summary: string | null;
  published_at: string | null;
  topics: ReviewTopic[];
  candidates: CandidateEvent[];
};

export type InviteCode = { id: number; code: string; used: boolean; used_at: string | null };

export async function getReview(): Promise<ReviewPayload> {
  return apiFetch<ReviewPayload>("/admin/review");
}
export async function approveTopic(id: number) {
  return apiFetch<{ ok: boolean }>(`/admin/topics/${id}/approve`, { method: "POST" });
}
export async function rejectTopic(id: number) {
  return apiFetch<void>(`/admin/topics/${id}`, { method: "DELETE" });
}
export async function editTopic(id: number, fields: Record<string, string>) {
  return apiFetch<ReviewTopic>(`/admin/topics/${id}`, { method: "PUT", body: JSON.stringify(fields) });
}
export async function addTopicFromEvent(eventId: number) {
  return apiFetch<{ ok: boolean }>(`/admin/topics`, { method: "POST", body: JSON.stringify({ event_id: eventId }) });
}
export async function publishReport() {
  return apiFetch<{ ok: boolean }>(`/admin/report/publish`, { method: "POST" });
}
export async function createInviteCodes(count: number): Promise<InviteCode[]> {
  return apiFetch<InviteCode[]>(`/admin/invite-codes`, { method: "POST", body: JSON.stringify({ count }) });
}
export async function listInviteCodes(): Promise<InviteCode[]> {
  return apiFetch<InviteCode[]>(`/admin/invite-codes`);
}
