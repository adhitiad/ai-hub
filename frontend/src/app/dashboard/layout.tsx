"use client";

import { MainNavbar } from "@/components/MainNavbar";
import { Sidebar } from "@/components/sidebar";
import { useAuthStore } from "@/stores/useAuthStore";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="relative min-h-screen flex w-full bg-background text-foreground transition-colors duration-500 overflow-x-hidden">
      {/* Background radial glow */}
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(16,185,129,0.05),transparent_70%)] pointer-events-none z-0" />

      {/* Sidebar - Fixed width 64 (256px) */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 w-full pl-64 min-h-screen relative transition-all duration-300 ease-in-out flex flex-col z-10">
        {/* Main Navbar with Search, Theme, Health */}
        <MainNavbar />

        <div className="flex-1 p-6 md:p-10 max-w-[1700px] w-full mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
          {children}
        </div>
      </main>
    </div>
  );
}
