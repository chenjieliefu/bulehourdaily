"use client";

import { useState, type CSSProperties, type ReactNode } from "react";
import { fmtDate, fmtTime } from "@/lib/format";
import type { Report, Topic } from "@/lib/api";
import styles from "./ReportView.module.css";

const LABEL: Record<string, string> = {
  official: "官方确认",
  multi_source: "多方报道",
  early_signal: "早期信号",
};

const ACCENTS = [
  { accent: "#397eaa", soft: "#eaf4fa", ink: "#194f71" },
  { accent: "#6e79a9", soft: "#eef0f8", ink: "#434f83" },
  { accent: "#d28b62", soft: "#fcf1e9", ink: "#945739" },
];

export default function ReportView({ report }: { report: Report }) {
  const [expandedId, setExpandedId] = useState<number | null>(null);

  return (
    <div className={styles.report}>
      <header className={styles.cover}>
        <div className={styles.coverCopy}>
          <div className={styles.kickerRow}>
            <span className={styles.kicker}>BLUE HOUR · DAILY BRIEF</span>
            <span className={styles.issueBadge}>第 {String(report.id).padStart(3, "0")} 期</span>
          </div>
          <time className={styles.date} dateTime={report.report_date}>
            {fmtDate(report.report_date)}
          </time>
          <h2 className={styles.coverTitle}>
            今天，先看这 <em>{report.topics.length}</em> 件事
          </h2>
          <p className={styles.summary}>{report.summary || "今日重点已经整理完毕。"}</p>
          <div className={styles.metaRow}>
            <span><i className={styles.liveDot} /> 已人工质检</span>
            <span>{report.briefs.length} 条速览</span>
            <span>更新于 {fmtTime(report.updated_at)}</span>
          </div>
        </div>

        <nav className={styles.issueIndex} aria-label="本期目录">
          <div className={styles.indexHeading}>
            <span>IN THIS ISSUE</span>
            <span>本期目录</span>
          </div>
          <ol>
            {report.topics.map((topic) => (
              <li key={topic.id}>
                <button
                  type="button"
                  onClick={() => {
                    setExpandedId(topic.id);
                    document.getElementById(`topic-${topic.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
                  }}
                >
                  <span>{String(topic.order_index).padStart(2, "0")}</span>
                  <strong>{topic.title}</strong>
                </button>
              </li>
            ))}
          </ol>
        </nav>
      </header>

      <section className={styles.section} aria-labelledby="daily-topics-title">
        <SectionHeading
          eyebrow="EDITOR'S PICKS"
          title="今日主选题"
          note="先读重点，需要时再展开创作建议"
          count={report.topics.length}
          id="daily-topics-title"
        />
        <div className={styles.topicList}>
          {report.topics.map((topic) => (
            <TopicCard
              key={topic.id}
              topic={topic}
              expanded={expandedId === topic.id}
              onToggle={() => setExpandedId(expandedId === topic.id ? null : topic.id)}
            />
          ))}
        </div>
      </section>

      {report.briefs.length > 0 && (
        <section className={styles.section} aria-labelledby="daily-briefs-title">
          <SectionHeading
            eyebrow="QUICK READS"
            title="今日速览"
            note="两分钟补齐其余重要动态"
            count={report.briefs.length}
            id="daily-briefs-title"
          />
          <div className={styles.briefGrid}>
            {report.briefs.map((brief) => (
              <article key={brief.id} className={styles.briefCard}>
                <div className={styles.briefTopline}>
                  <span>BRIEF {String(brief.order_index).padStart(2, "0")}</span>
                  <time>{fmtTime(brief.event_published_at)}</time>
                </div>
                <p>{brief.summary}</p>
                {brief.evidence.length > 0 && (
                  <a href={brief.evidence[0].url} target="_blank" rel="noopener noreferrer">
                    来源：{brief.evidence[0].source_name}
                    <span aria-hidden>↗</span>
                  </a>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      <footer className={styles.reportFooter}>
        <span>BLUE HOUR DAILY</span>
        <p>只保留值得你花时间的变化。</p>
      </footer>
    </div>
  );
}

function SectionHeading({ eyebrow, title, note, count, id }: { eyebrow: string; title: string; note: string; count: number; id: string }) {
  return (
    <div className={styles.sectionHeading}>
      <div>
        <span>{eyebrow}</span>
        <h2 id={id}>{title}</h2>
      </div>
      <p>{note}</p>
      <strong>{String(count).padStart(2, "0")}</strong>
    </div>
  );
}

function TopicCard({ topic, expanded, onToggle }: { topic: Topic; expanded: boolean; onToggle: () => void }) {
  const accent = ACCENTS[(topic.order_index - 1) % ACCENTS.length];
  const cssVars = {
    "--topic-accent": accent.accent,
    "--topic-soft": accent.soft,
    "--topic-ink": accent.ink,
  } as CSSProperties;
  const panelId = `topic-details-${topic.id}`;

  return (
    <article id={`topic-${topic.id}`} className={`${styles.topicCard} ${expanded ? styles.topicExpanded : ""}`} style={cssVars}>
      <button
        type="button"
        className={styles.topicButton}
        onClick={onToggle}
        aria-expanded={expanded}
        aria-controls={panelId}
      >
        <span className={styles.topicNumber}>{String(topic.order_index).padStart(2, "0")}</span>
        <span className={styles.topicCopy}>
          <span className={styles.topicMeta}>
            <span>{topic.credibility_label ? LABEL[topic.credibility_label] : "信息待核"}</span>
            <time>{fmtTime(topic.event_published_at)}</time>
          </span>
          <strong className={styles.topicTitle}>{topic.title}</strong>
          <span className={styles.topicSummary}>{topic.what_happened}</span>
        </span>
        <span className={styles.topicToggle} aria-hidden>
          <span>{expanded ? "收起" : "展开"}</span>
          <svg viewBox="0 0 24 24" focusable="false">
            <path d={expanded ? "m6 15 6-6 6 6" : "m6 9 6 6 6-6"} />
          </svg>
        </span>
      </button>

      {expanded && (
        <div id={panelId} className={styles.topicDetails}>
          <div className={styles.hookBlock}>
            <span>开场钩子</span>
            <p>“{topic.hook}”</p>
          </div>

          <div className={styles.detailGrid}>
            <Detail label="为什么值得关注">{topic.why_now}</Detail>
            <Detail label="推荐切入角度">{topic.angle}</Detail>
            <Detail label="内容结构" wide>{topic.structure}</Detail>
            <Detail label="画面建议">{topic.visual}</Detail>
            <Detail label="建议发布时机" highlighted>{topic.time_window}</Detail>
          </div>

          <div className={styles.evidenceRow}>
            <span>原始来源</span>
            <div>
              {topic.evidence.length === 0 && <span>暂无来源</span>}
              {topic.evidence.map((evidence) => (
                <a key={evidence.source_item_id} href={evidence.url} target="_blank" rel="noopener noreferrer">
                  {evidence.source_name}
                  <span aria-hidden>↗</span>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </article>
  );
}

function Detail({ label, children, wide = false, highlighted = false }: { label: string; children: ReactNode; wide?: boolean; highlighted?: boolean }) {
  return (
    <div className={`${styles.detailBlock} ${wide ? styles.detailWide : ""} ${highlighted ? styles.detailHighlighted : ""}`}>
      <span>{label}</span>
      <p>{children}</p>
    </div>
  );
}
