"use client";

import { Suspense, useEffect, useState } from "react";
import LandingPrototype from "./LandingPrototype";
import { getPublicSiteContent } from "@/lib/api";

const DEFAULT_CONTENT = {
  eyebrow: "Blue Hour Daily · 08:00",
  title: "在世界醒来之前，看见下一刻。",
  subtitle: "每天 08:00，把海外最新 AI 动态，变成三个值得拍的抖音选题。",
  section_title: "每天一份日报，把「看信息」变成「拍什么」。",
  features: [
    { title: "不漏掉", detail: "盯着 40+ 海外 AI 信息源，每天 08:00 汇总最新动态。" },
    { title: "会判断", detail: "聚成热点事件，标注可信度，告诉你哪个值得跟进。" },
    { title: "能行动", detail: "每个选题给出钩子、结构、画面建议，直接开拍。" },
  ],
};

export default function LandingPage() {
  const [content, setContent] = useState(DEFAULT_CONTENT);
  useEffect(() => {
    getPublicSiteContent("product_intro").then((row) => setContent({ ...DEFAULT_CONTENT, ...row.content } as typeof DEFAULT_CONTENT)).catch(() => undefined);
  }, []);

  return (
    <Suspense fallback={<div className="min-h-screen bg-[#194967]" />}>
      <LandingPrototype content={content} />
    </Suspense>
  );
}
