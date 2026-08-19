"""邮件送达：MVP 本地模拟发送（写记录 + 日志，不真发）。"""
import logging

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import MailDelivery, PersonalizedReport, PersonalizedTopic, User
from app.models.enums import MailStatus

logger = logging.getLogger("weilan.mail")


def send_personalized_mail(db: Session, user: User, report: PersonalizedReport, topics: list[PersonalizedTopic]) -> MailDelivery:
    subject = f"微蓝日报 · {report.report_date} 个性化日报"
    lines = [f"{t.order_index}. {t.title}" for t in topics[:3]]
    body = "今天为你的账号推荐：\n" + "\n".join(lines) + "\n\n查看：http://127.0.0.1:3000/mine"

    delivery = MailDelivery(
        user_id=user.id,
        report_id=report.id,
        subject=subject,
        body=body,
        status=MailStatus.sent,  # 模拟直接成功
        sent_at=utcnow(),
    )
    db.add(delivery)
    db.flush()

    # 本地模拟：只写日志，不真发
    logger.info("[模拟发信] to=%s subject=%s", user.email, subject)
    return delivery
