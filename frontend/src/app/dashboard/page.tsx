"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Sidebar } from "@/components/sidebar";
import { DashboardOverview } from "@/components/dashboard-overview";

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <main className="flex-1 ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 flex items-center justify-between px-8 py-4 border-b border-white/10 glass-panel">
          <div>
            <h2 className="text-lg font-bold">Dashboard</h2>
            <p className="text-xs text-muted-foreground">
              リアルタイムモニター — Real-time Trading Monitor
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-trade-up/10 border border-trade-up/20">
              <div className="w-2 h-2 rounded-full bg-trade-up animate-pulse" />
              <span className="text-[11px] font-medium text-trade-up">LIVE</span>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-8">
          <DashboardOverview />
        </div>
      </main>
    </div>
  );
}
