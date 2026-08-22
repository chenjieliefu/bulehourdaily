import DailyReviewPanel from "@/app/components/operations/DailyReviewPanel";
import TodayPipelinePanel from "@/app/components/operations/TodayPipelinePanel";
import { OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function OperationsOverviewPage() {
  return (
    <>
      <OperationsPageHeader
        eyebrow="Daily Operations"
        title="今日工作台"
        description="从信息采集到正式发布，一页完成今天的日报运营。"
        actions={<a href="/" target="_blank" rel="noopener noreferrer" className="rounded-full border border-steel bg-white px-4 py-2 text-xs text-fog hover:border-cyan hover:text-cyan">查看公开日报 ↗</a>}
      />
      <OperationsSection>
        <div className="space-y-12">
          <TodayPipelinePanel />
          <DailyReviewPanel />
        </div>
      </OperationsSection>
    </>
  );
}
