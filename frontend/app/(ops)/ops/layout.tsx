import OperationsShell from "@/app/components/operations/OperationsShell";

export default function OpsLayout({ children }: { children: React.ReactNode }) {
  return <OperationsShell>{children}</OperationsShell>;
}
