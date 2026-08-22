import Link from "next/link";
import { OperationsPageHeader, OperationsSection } from "@/app/components/operations/OperationsPage";

export default function MembershipSiteOperationsPage() {
  return (
    <>
      <OperationsPageHeader
        eyebrow="Retired Entry"
        title="会员页面编辑已停用"
        description="用户端升级会员页面仍然保留；等会员方案确定后，再直接替换用户端版本。"
      />
      <OperationsSection>
        <div className="paper-card rounded-card p-8">
          <p className="text-sm leading-7 text-fog">这个入口不再承担运营工作，也不会修改当前用户端页面。</p>
          <Link href="/ops" className="mt-5 inline-flex rounded-full bg-cyan px-5 py-2.5 text-sm text-white">返回今日工作台</Link>
        </div>
      </OperationsSection>
    </>
  );
}
