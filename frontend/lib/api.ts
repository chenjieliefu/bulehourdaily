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

export type ReportSummary = {
  id: number;
  report_date: string;
  status: "draft" | "published";
  summary: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Report = ReportSummary & {
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

export type ProductFeedbackCategory =
  | "bug"
  | "content"
  | "experience"
  | "membership"
  | "suggestion"
  | "other";

export type ProductFeedbackReceipt = {
  id: number;
  category: ProductFeedbackCategory;
  status: string;
  created_at: string;
};

const BASE = "/api/v1";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

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
    throw new ApiError(body?.detail || `请求失败（${res.status}）`, res.status);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---- 公开日报 ----
export async function listReports(): Promise<ReportSummary[]> {
  return apiFetch<ReportSummary[]>("/reports");
}
export async function getLatestReport(): Promise<Report | null> {
  return apiFetch<Report | null>("/reports/latest");
}
export async function getReport(id: number): Promise<Report> {
  return apiFetch<Report>(`/reports/${id}`);
}

// ---- 鉴权 ----
export async function apiRegister(email: string, password: string, invite_code: string) {
  return apiFetch<{ token: string; user: { id: number; email: string; is_operator: boolean } }>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, invite_code }),
  });
}
export async function apiLogin(email: string, password: string) {
  return apiFetch<{ token: string; user: { id: number; email: string; is_operator: boolean } }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
export async function apiCurrentUser() {
  return apiFetch<{ id: number; email: string; is_operator: boolean }>("/auth/me");
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

// ---- 产品意见反馈 ----
export async function submitProductFeedback(payload: {
  category: ProductFeedbackCategory;
  content: string;
  contact_email?: string;
  page_url?: string;
}): Promise<ProductFeedbackReceipt> {
  return apiFetch<ProductFeedbackReceipt>("/product-feedback", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
  is_published: boolean;
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

export type OperationsOverview = {
  report_date: string;
  public_report_status: "draft" | "published" | null;
  unreviewed_topics: number;
  creators_total: number;
  profiles_completed: number;
  active_subscribers: number;
  trial_creators: number;
  trial_exhausted: number;
  expiring_subscribers: number;
  today_personalized_reports: number;
  today_personalized_expected: number;
  failed_mail_deliveries: number;
  new_product_feedback: number;
};

export type CreatorOperations = {
  id: number;
  email: string;
  created_at: string;
  has_profile: boolean;
  profile_positioning: string | null;
  entitlement_status: "subscriber" | "trial" | "trial_exhausted" | "expired";
  trial_remaining: number;
  subscription_price_type: string | null;
  subscription_monthly_price: number | null;
  subscription_expires_at: string | null;
  personalized_report_count: number;
  last_report_date: string | null;
  creation_plan_count: number;
  feedback_want: number;
  feedback_not_interested: number;
  feedback_published: number;
  latest_mail_status: string | null;
  latest_interaction_at: string | null;
  product_feedback_count: number;
};

export type PersonalizedOperationsPlan = {
  core_viewpoint: string;
  hooks: string[];
  structure: string;
  visual: string;
  titles: string[];
  risks: string;
};

export type PersonalizedOperationsTopic = {
  id: number;
  order_index: number;
  title: string;
  what_happened: string;
  why_now: string;
  angle: string;
  hook: string;
  structure: string;
  visual: string;
  time_window: string;
  recommendation_reason: string;
  credibility_label: CredibilityLabel | null;
  evidence: EvidenceItem[];
  feedback_status: "want" | "not_interested" | "published" | null;
  feedback_douyin_url: string | null;
  plan: PersonalizedOperationsPlan | null;
};

export type PersonalizedOperationsReport = {
  id: number;
  user_id: number;
  email: string;
  report_date: string;
  summary: string | null;
  reason: string | null;
  created_at: string;
  mail_status: string | null;
  topics: PersonalizedOperationsTopic[];
};

export type ProductFeedbackOperations = {
  id: number;
  user_id: number | null;
  user_email: string | null;
  category: ProductFeedbackCategory;
  content: string;
  contact_email: string | null;
  page_url: string | null;
  status: "new" | "in_progress" | "resolved";
  created_at: string;
};

export type EventOperations = {
  id: number;
  title: string;
  summary: string;
  credibility_label: CredibilityLabel;
  relevance_score: number;
  actionability_score: number;
  freshness_score: number;
  sort_score: number;
  reason: string | null;
  status: string;
  first_seen_at: string;
  evidence_count: number;
};

export type MailDeliveryOperations = {
  id: number;
  user_id: number;
  user_email: string;
  report_id: number | null;
  report_date: string | null;
  subject: string;
  status: string;
  error: string | null;
  created_at: string;
  sent_at: string | null;
};

export type SubscriptionOperations = {
  id: number;
  user_id: number;
  user_email: string;
  price_type: string;
  monthly_price: number;
  status: string;
  started_at: string;
  expires_at: string;
  is_effective: boolean;
};

export type PublicationFeedbackOperations = {
  id: number;
  user_id: number;
  user_email: string;
  report_id: number;
  report_date: string;
  topic_id: number;
  topic_title: string;
  status: string;
  douyin_url: string | null;
  updated_at: string;
};

export type JobOperations = Job & {
  context: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
};

export type SourceOperations = {
  id: number;
  name: string;
  type: string;
  url: string;
  enabled: boolean;
  credibility_level: string;
  max_items_per_day: number;
  created_at: string;
  updated_at: string;
};

export type CollectionStatus = {
  last_collect_at: string | null;
  total_sources: number;
  enabled_sources: number;
  total_items: number;
  sources: Array<{
    source_id: number;
    source_name: string;
    type: string;
    credibility_level: string;
    max_items_per_day: number;
    enabled: boolean;
    last_success_at: string | null;
    last_status: string | null;
    last_error: string | null;
  }>;
};

export type SiteContentKey = "product_intro" | "membership";
export type SiteContentOperations = {
  key: SiteContentKey;
  draft: Record<string, unknown>;
  published: Record<string, unknown>;
  previous_published: Record<string, unknown> | null;
  updated_at: string;
  published_at: string | null;
};
export type SiteContentPublic = {
  key: SiteContentKey;
  content: Record<string, unknown>;
  published_at: string | null;
};

export async function getReview(): Promise<ReviewPayload> {
  return apiFetch<ReviewPayload>("/admin/review");
}
export async function getOperationsOverview(): Promise<OperationsOverview> {
  return apiFetch<OperationsOverview>("/admin/overview");
}
export async function listCreatorOperations(): Promise<CreatorOperations[]> {
  return apiFetch<CreatorOperations[]>("/admin/creators");
}
export async function listPersonalizedOperations(filters: {
  userId?: number;
  reportDate?: string;
} = {}): Promise<PersonalizedOperationsReport[]> {
  const params = new URLSearchParams();
  if (filters.userId) params.set("user_id", String(filters.userId));
  if (filters.reportDate) params.set("report_date", filters.reportDate);
  const query = params.size ? `?${params.toString()}` : "";
  return apiFetch<PersonalizedOperationsReport[]>(`/admin/personalized-reports${query}`);
}
export async function listProductFeedbackOperations(
  status?: ProductFeedbackOperations["status"],
): Promise<ProductFeedbackOperations[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<ProductFeedbackOperations[]>(`/admin/product-feedback${query}`);
}
export async function updateProductFeedbackOperations(
  id: number,
  status: ProductFeedbackOperations["status"],
): Promise<ProductFeedbackOperations> {
  return apiFetch<ProductFeedbackOperations>(`/admin/product-feedback/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
export async function approveTopic(id: number) {
  return apiFetch<{ ok: boolean }>(`/admin/topics/${id}/approve`, { method: "POST" });
}
export async function removeTopic(id: number) {
  return apiFetch<void>(`/admin/topics/${id}`, { method: "DELETE" });
}
export async function unpublishTopic(id: number) {
  return apiFetch<{ ok: boolean }>(`/admin/topics/${id}/unpublish`, { method: "POST" });
}
export async function republishTopic(id: number) {
  return apiFetch<{ ok: boolean }>(`/admin/topics/${id}/republish`, { method: "POST" });
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
export async function unpublishReport() {
  return apiFetch<{ ok: boolean }>(`/admin/report/unpublish`, { method: "POST" });
}
export async function createInviteCodes(count: number): Promise<InviteCode[]> {
  return apiFetch<InviteCode[]>(`/admin/invite-codes`, { method: "POST", body: JSON.stringify({ count }) });
}
export async function listInviteCodes(): Promise<InviteCode[]> {
  return apiFetch<InviteCode[]>(`/admin/invite-codes`);
}

export async function listEventsOperations(): Promise<EventOperations[]> {
  return apiFetch<EventOperations[]>("/events");
}
export async function listMailDeliveriesOperations(): Promise<MailDeliveryOperations[]> {
  return apiFetch<MailDeliveryOperations[]>("/admin/mail-deliveries");
}
export async function listSubscriptionsOperations(): Promise<SubscriptionOperations[]> {
  return apiFetch<SubscriptionOperations[]>("/admin/subscriptions");
}
export async function createSubscriptionOperations(payload: {
  user_id: number;
  months: number;
  price_type?: "founding" | "standard";
}): Promise<SubscriptionOperations> {
  return apiFetch<SubscriptionOperations>("/admin/subscriptions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
export async function listPublicationFeedbackOperations(): Promise<PublicationFeedbackOperations[]> {
  return apiFetch<PublicationFeedbackOperations[]>("/admin/publication-feedback");
}
export async function listJobsOperations(): Promise<JobOperations[]> {
  return apiFetch<JobOperations[]>("/admin/jobs");
}
export async function listSourcesOperations(): Promise<SourceOperations[]> {
  return apiFetch<SourceOperations[]>("/sources");
}
export async function updateSourceOperations(
  id: number,
  payload: Partial<Pick<SourceOperations, "name" | "url" | "enabled" | "credibility_level" | "max_items_per_day">>,
): Promise<SourceOperations> {
  return apiFetch<SourceOperations>(`/sources/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}
export async function getCollectionStatus(): Promise<CollectionStatus> {
  return apiFetch<CollectionStatus>("/status");
}
export async function getSiteContentOperations(key: SiteContentKey): Promise<SiteContentOperations> {
  return apiFetch<SiteContentOperations>(`/admin/site-content/${key}`);
}
export async function saveSiteContentDraft(
  key: SiteContentKey,
  content: Record<string, unknown>,
): Promise<SiteContentOperations> {
  return apiFetch<SiteContentOperations>(`/admin/site-content/${key}/draft`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
}
export async function publishSiteContentOperations(key: SiteContentKey): Promise<SiteContentOperations> {
  return apiFetch<SiteContentOperations>(`/admin/site-content/${key}/publish`, { method: "POST" });
}
export async function rollbackSiteContentOperations(key: SiteContentKey): Promise<SiteContentOperations> {
  return apiFetch<SiteContentOperations>(`/admin/site-content/${key}/rollback`, { method: "POST" });
}
export async function getPublicSiteContent(key: SiteContentKey): Promise<SiteContentPublic> {
  return apiFetch<SiteContentPublic>(`/site-content/${key}`);
}
