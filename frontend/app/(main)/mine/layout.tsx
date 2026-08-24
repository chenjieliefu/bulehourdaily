import RequireUser from "@/app/components/RequireUser";

export default function MineLayout({ children }: { children: React.ReactNode }) {
  return <RequireUser>{children}</RequireUser>;
}
