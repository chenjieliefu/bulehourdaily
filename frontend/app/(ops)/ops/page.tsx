"use client";

import { useState } from "react";
import DailyReviewPanel from "@/app/components/operations/DailyReviewPanel";
import TodayPipelinePanel from "@/app/components/operations/TodayPipelinePanel";
import { OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function OperationsOverviewPage() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <>
      <OperationsPageHeader
        eyebrow="Daily Operations"
        title="今日工作台"
        description="从信息采集到正式发布，一页完成今天的日报运营。"
      />
      <OperationsSection>
        <div className="space-y-12">
          <TodayPipelinePanel refreshKey={refreshKey} />
          <DailyReviewPanel onChanged={() => setRefreshKey((value) => value + 1)} />
        </div>
      </OperationsSection>
    </>
  );
}
