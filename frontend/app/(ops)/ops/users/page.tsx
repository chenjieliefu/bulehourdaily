import BetaUsersPanel from "@/app/components/operations/BetaUsersPanel";
import { OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function BetaUsersOperationsPage() {
  return (
    <>
      <OperationsPageHeader
        eyebrow="Private Beta"
        title="内测用户"
        description="集中查看受邀用户和邀请码；订阅、邮件与个性化运营暂不放进当前工作流。"
      />
      <OperationsSection><BetaUsersPanel /></OperationsSection>
    </>
  );
}
