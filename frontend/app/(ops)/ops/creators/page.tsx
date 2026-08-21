"use client";

import { useRouter } from "next/navigation";
import CreatorsPanel from "@/app/components/operations/CreatorsPanel";
import { OperationsSection } from "@/app/components/operations/OperationsPage";

export default function CreatorsOperationsPage() {
  const router = useRouter();
  return <OperationsSection><CreatorsPanel onInspect={(id) => router.push(`/ops/personalized?user=${id}`)} /></OperationsSection>;
}
