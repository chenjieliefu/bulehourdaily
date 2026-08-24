import RequireUser from "@/app/components/RequireUser";

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return <RequireUser>{children}</RequireUser>;
}
