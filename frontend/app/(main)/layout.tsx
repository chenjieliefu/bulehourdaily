import Sidebar from "@/app/components/Sidebar";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-obsidian lg:flex">
      <Sidebar />
      <main className="flex-1 px-6 pb-24 lg:px-10">{children}</main>
    </div>
  );
}
