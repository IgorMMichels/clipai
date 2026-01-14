import { AppSidebar } from "@/components/ui/app-sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="dark">
      <AppSidebar>{children}</AppSidebar>
    </div>
  );
}
