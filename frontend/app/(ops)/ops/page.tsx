"use client";

import { useRouter } from "next/navigation";
import OverviewPanel from "@/app/components/operations/OverviewPanel";
import { OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

const ROUTES = {
  overview: "/ops",
  daily: "/ops/daily",
  creators: "/ops/creators",
  personalized: "/ops/personalized",
  feedback: "/ops/product-feedback",
};

export default function OperationsOverviewPage() {
  const router = useRouter();
  return <>
    <OperationsPageHeader eyebrow="Operations Overview" title="运营概览" description="先看今日异常和待办，再进入对应业务页面处理。" />
    <OperationsSection><OverviewPanel onOpen={(key) => router.push(ROUTES[key])} /></OperationsSection>
  </>;
}
