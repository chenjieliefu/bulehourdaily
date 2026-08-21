"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getMySubscription, getPublicSiteContent, type Subscription } from "@/lib/api";
import { isLoggedIn } from "@/lib/auth";

type ViewerState = "loading" | "guest" | "free" | "member" | "error";

const MEMBER_BENEFITS = [
  { title: "每日 3 个个性化选题", detail: "按你的账号定位、受众和内容风格，从当天热点中重新选择。" },
  { title: "一键展开创作方案", detail: "获得开场钩子、内容结构、画面建议、标题方向和风险提示。" },
  { title: "每日邮件送达", detail: "日报生成后主动送达，减少反复打开产品查看的成本。" },
  { title: "发布反馈持续优化", detail: "记录想做、不感兴趣和已发布，让后续推荐越来越贴合你。" },
  { title: "历史个性化日报", detail: "保留资格有效期间生成的个性化内容，随时回看。" },
  { title: "保留全部公共权益", detail: "继续访问完整公开日报、证据来源、可信度标签和往期归档。" },
];

const COMPARISON = [
  ["每日完整公开日报", true, true],
  ["证据来源与可信度标签", true, true],
  ["公开日报往期归档", true, true],
  ["按创作者画像生成选题", false, true],
  ["展开详细创作方案", false, true],
  ["每日个性化邮件", false, true],
  ["历史个性化日报", false, true],
] as const;

const DEFAULT_CONTENT = {
  title: "升级会员",
  subtitle: "通用日报看今天，个性化日报看「适合我的今天」。",
  hero_title: "少刷一小时信息流，每天多一个可以开拍的选题。",
  hero_detail: "会员不是给你更多资讯，而是基于你的账号画像，把当天真正适合你的热点转成可行动的创作方案。",
  trial_title: "注册后免费获得 3 份个性化日报",
  trial_detail: "体验按成功生成的日报份数计算，不绑定支付方式。体验结束后仍可继续阅读公开日报。",
};

export default function UpgradePage() {
  const [viewerState, setViewerState] = useState<ViewerState>("loading");
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [content, setContent] = useState(DEFAULT_CONTENT);

  useEffect(() => {
    (async () => {
      getPublicSiteContent("membership").then((row) => setContent({ ...DEFAULT_CONTENT, ...row.content } as typeof DEFAULT_CONTENT)).catch(() => undefined);
      if (!isLoggedIn()) {
        setViewerState("guest");
        return;
      }

      try {
        const current = await getMySubscription();
        setSubscription(current);
        setViewerState(current ? "member" : "free");
      } catch {
        setViewerState("error");
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-[1080px] pb-20">
      <header className="flex flex-col gap-4 border-b border-steel/80 pb-6 pt-8 sm:flex-row sm:items-end sm:justify-between lg:pt-10">
        <div>
          <p className="eyebrow">Membership</p>
          <h1 className="mt-2 font-serif text-3xl text-cloud md:text-4xl">{content.title}</h1>
        </div>
        <p className="max-w-md text-sm leading-relaxed text-fog sm:text-right">
          {content.subtitle}
        </p>
      </header>

      <section className="report-cover mt-8 rounded-feature border border-white/80 px-7 py-10 sm:px-10 sm:py-12">
        <div className="relative grid gap-10 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-end">
          <div>
            <p className="eyebrow text-deep-iris">Blue Hour Membership</p>
            <h2 className="mt-5 max-w-2xl font-serif text-3xl leading-tight text-cloud sm:text-4xl">
              {content.hero_title}
            </h2>
            <p className="mt-5 max-w-xl text-sm leading-7 text-ash">
              {content.hero_detail}
            </p>
          </div>

          <div className="rounded-feature border border-white/80 bg-white/70 p-6 shadow-[0_18px_45px_rgba(50,91,116,0.10)] backdrop-blur-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="rounded-full border border-orchid/35 bg-orange-50 px-3 py-1 text-xs text-amber-700">
                前 50 位创始用户
              </span>
              <span className="font-mono text-[10px] uppercase tracking-widest text-fog">按月订阅</span>
            </div>
            <div className="mt-5 flex items-end gap-2 text-cloud">
              <span className="pb-1 font-serif text-2xl">¥</span>
              <span className="font-serif text-6xl leading-none">29</span>
              <span className="pb-1 text-sm text-fog">/ 月</span>
            </div>
            <p className="mt-3 text-sm text-fog">连续订阅期间保留创始价格，标准价 ¥49/月。</p>
            <MembershipAction state={viewerState} subscription={subscription} />
          </div>
        </div>
      </section>

      {viewerState === "member" && subscription && (
        <section className="paper-card mt-6 flex flex-col gap-4 rounded-card p-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="eyebrow">当前会员</p>
            <p className="mt-2 text-sm text-ash">
              你的会员正在生效 · ¥{subscription.monthly_price}/月 · {subscription.price_type === "founding" ? "创始会员" : "标准会员"}
            </p>
          </div>
          <p className="shrink-0 font-mono text-xs text-cyan">有效至 {formatMembershipDate(subscription.expires_at)}</p>
        </section>
      )}

      <section className="mt-14">
        <div className="flex items-center gap-4">
          <h2 className="eyebrow shrink-0">会员能得到什么</h2>
          <span className="section-rule" />
          <span className="font-mono text-xs text-fog">06</span>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {MEMBER_BENEFITS.map((benefit, index) => (
            <article key={benefit.title} className="paper-card rounded-card p-6">
              <span className="font-serif text-2xl text-periwinkle">{String(index + 1).padStart(2, "0")}</span>
              <h3 className="mt-4 font-serif text-lg text-cloud">{benefit.title}</h3>
              <p className="mt-2 text-sm leading-6 text-fog">{benefit.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <div className="flex items-center gap-4">
          <h2 className="eyebrow shrink-0">免费与会员</h2>
          <span className="section-rule" />
        </div>
        <div className="paper-card mt-5 overflow-hidden rounded-feature">
          <div className="grid grid-cols-[minmax(0,1fr)_72px_72px] border-b border-steel bg-abyss/50 px-5 py-4 text-xs sm:grid-cols-[minmax(0,1fr)_120px_120px] sm:px-7">
            <span className="font-mono uppercase tracking-widest text-fog">权益</span>
            <span className="text-center text-fog">免费</span>
            <span className="text-center text-cyan">会员</span>
          </div>
          {COMPARISON.map(([label, free, member]) => (
            <div key={label} className="grid grid-cols-[minmax(0,1fr)_72px_72px] items-center border-b border-steel/80 px-5 py-4 text-sm last:border-b-0 sm:grid-cols-[minmax(0,1fr)_120px_120px] sm:px-7">
              <span className="text-ash">{label}</span>
              <ComparisonMark included={free} />
              <ComparisonMark included={member} />
            </div>
          ))}
        </div>
      </section>

      <section className="paper-card mt-14 rounded-feature p-7 sm:p-9">
        <div className="grid gap-8 md:grid-cols-[minmax(0,1fr)_280px] md:items-center">
          <div>
            <p className="eyebrow">先体验，再决定</p>
            <h2 className="mt-3 font-serif text-2xl text-cloud">{content.trial_title}</h2>
            <p className="mt-3 text-sm leading-7 text-fog">
              {content.trial_detail}
            </p>
          </div>
          <div className="rounded-card border border-steel bg-abyss/45 p-5 text-sm leading-6 text-silver">
            <p className="font-medium text-cloud">当前开通方式</p>
            <p className="mt-2">MVP 阶段由运营者人工确认付款并开通，暂未接入自动支付。</p>
          </div>
        </div>
      </section>
    </div>
  );
}

function MembershipAction({ state, subscription }: { state: ViewerState; subscription: Subscription | null }) {
  if (state === "loading") {
    return <div className="mt-6 h-11 animate-pulse rounded-full bg-pale-iris/70" />;
  }

  if (state === "member" && subscription) {
    return (
      <Link href="/mine" className="mt-6 block rounded-full bg-cyan px-6 py-3 text-center text-sm font-medium text-white transition-opacity hover:opacity-90">
        查看我的个性化日报
      </Link>
    );
  }

  if (state === "free") {
    return (
      <Link href="/mine" className="mt-6 block rounded-full bg-cyan px-6 py-3 text-center text-sm font-medium text-white transition-opacity hover:opacity-90">
        先使用免费体验
      </Link>
    );
  }

  return (
    <div className="mt-6 grid gap-2">
      <Link href="/register" className="block rounded-full bg-cyan px-6 py-3 text-center text-sm font-medium text-white transition-opacity hover:opacity-90">
        用邀请码开始体验
      </Link>
      <Link href="/login" className="text-center text-xs text-fog transition-colors hover:text-cyan">
        已有账号，直接登录
      </Link>
    </div>
  );
}

function ComparisonMark({ included }: { included: boolean }) {
  return (
    <span className={`text-center text-sm ${included ? "text-cyan" : "text-fog/45"}`} aria-label={included ? "包含" : "不包含"}>
      {included ? "✓" : "—"}
    </span>
  );
}

function formatMembershipDate(value: string) {
  const normalized = /[zZ]|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`;
  return new Date(normalized).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
