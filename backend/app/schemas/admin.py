"""运营工作台接口结构。"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CredibilityLabel, ReportStatus
from .event import EvidenceItem


class TopicEdit(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    what_happened: str | None = None
    why_now: str | None = None
    angle: str | None = None
    hook: str | None = None
    structure: str | None = None
    visual: str | None = None
    time_window: str | None = None


class ReviewTopic(BaseModel):
    id: int
    title: str
    what_happened: str
    why_now: str
    angle: str
    hook: str
    structure: str
    visual: str
    time_window: str
    order_index: int
    hot_event_id: int
    credibility_label: CredibilityLabel | None = None
    reviewed: bool
    evidence: list[EvidenceItem] = []


class CandidateEvent(BaseModel):
    id: int
    title: str
    summary: str
    credibility_label: CredibilityLabel
    sort_score: float
    evidence_count: int


class ReviewPayload(BaseModel):
    report_id: int | None
    report_date: date | None
    status: ReportStatus | None
    summary: str | None
    published_at: datetime | None
    topics: list[ReviewTopic] = []
    candidates: list[CandidateEvent] = []


class AddTopicRequest(BaseModel):
    event_id: int


class InviteCodeCreate(BaseModel):
    count: int = Field(default=5, ge=1, le=100)


class InviteCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    used: bool
    used_at: datetime | None


EntitlementStatus = Literal["subscriber", "trial", "trial_exhausted", "expired"]
ProductFeedbackStatus = Literal["new", "in_progress", "resolved"]


class OperationsOverview(BaseModel):
    report_date: date
    public_report_status: ReportStatus | None
    unreviewed_topics: int
    creators_total: int
    profiles_completed: int
    active_subscribers: int
    trial_creators: int
    trial_exhausted: int
    expiring_subscribers: int
    today_personalized_reports: int
    today_personalized_expected: int
    failed_mail_deliveries: int
    new_product_feedback: int


class CreatorOperationsRead(BaseModel):
    id: int
    email: str
    created_at: datetime
    has_profile: bool
    profile_positioning: str | None
    entitlement_status: EntitlementStatus
    trial_remaining: int
    subscription_price_type: str | None
    subscription_monthly_price: int | None
    subscription_expires_at: datetime | None
    personalized_report_count: int
    last_report_date: date | None
    creation_plan_count: int
    feedback_want: int
    feedback_not_interested: int
    feedback_published: int
    latest_mail_status: str | None
    latest_interaction_at: datetime | None
    product_feedback_count: int


class PersonalizedPlanRead(BaseModel):
    core_viewpoint: str
    hooks: list[str] = []
    structure: str
    visual: str
    titles: list[str] = []
    risks: str


class PersonalizedContentTopic(BaseModel):
    id: int
    order_index: int
    title: str
    what_happened: str
    why_now: str
    angle: str
    hook: str
    structure: str
    visual: str
    time_window: str
    recommendation_reason: str
    credibility_label: CredibilityLabel | None
    evidence: list[EvidenceItem] = []
    feedback_status: str | None
    feedback_douyin_url: str | None
    plan: PersonalizedPlanRead | None


class PersonalizedContentReport(BaseModel):
    id: int
    user_id: int
    email: str
    report_date: date
    summary: str | None
    reason: str | None
    created_at: datetime
    mail_status: str | None
    topics: list[PersonalizedContentTopic] = []


class ProductFeedbackOperationsRead(BaseModel):
    id: int
    user_id: int | None
    user_email: str | None
    category: str
    content: str
    contact_email: str | None
    page_url: str | None
    status: ProductFeedbackStatus
    created_at: datetime


class ProductFeedbackStatusUpdate(BaseModel):
    status: ProductFeedbackStatus


class MailDeliveryOperationsRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    report_id: int | None
    report_date: date | None
    subject: str
    status: str
    error: str | None
    created_at: datetime
    sent_at: datetime | None


class SubscriptionOperationsRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    price_type: str
    monthly_price: int
    status: str
    started_at: datetime
    expires_at: datetime
    is_effective: bool


class SubscriptionOperationsCreate(BaseModel):
    user_id: int
    months: int = Field(default=1, ge=1, le=12)
    price_type: Literal["founding", "standard"] | None = None


class PublicationFeedbackOperationsRead(BaseModel):
    id: int
    user_id: int
    user_email: str
    report_id: int
    report_date: date
    topic_id: int
    topic_title: str
    status: str
    douyin_url: str | None
    updated_at: datetime


class JobOperationsRead(BaseModel):
    id: int
    kind: str
    status: str
    result_ref: str | None
    error_message: str | None
    context: dict | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
