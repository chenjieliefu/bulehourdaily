"use client";

import { useSearchParams } from "next/navigation";
import PersonalizedPanel from "@/app/components/operations/PersonalizedPanel";
import { OperationsSection } from "@/app/components/operations/OperationsPage";

export default function PersonalizedOperationsPage() {
  const params = useSearchParams();
  const userId = Number(params.get("user")) || null;
  return <OperationsSection><PersonalizedPanel key={userId ?? "all"} initialUserId={userId} /></OperationsSection>;
}
