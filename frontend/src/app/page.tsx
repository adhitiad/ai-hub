"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { Zap, ArrowRight, TrendingUp, Shield, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function Home() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen relative overflow-hidden px-6">
      {/* Background effects */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] rounded-full bg-emerald-500/8 blur-3xl" />
        <div className="absolute bottom-0 left-1/4 w-[500px] h-[300px] rounded-full bg-purple-600/8 blur-3xl" />
        <div className="absolute top-1/3 right-0 w-[400px] h-[400px] rounded-full bg-pink-500/5 blur-3xl" />
      </div>
      <div
        className="absolute inset-0 -z-10 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
          backgroundSize: "50px 50px",
        }}
      />

      {/* Hero */}
      <div className="text-center space-y-8 max-w-2xl">
        {/* Logo */}
        <div className="mx-auto w-20 h-20 rounded-2xl bg-gradient-to-br from-emerald-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-emerald-500/25 relative">
          <Zap className="w-10 h-10 text-white" />
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-400 animate-pulse border-2 border-background" />
        </div>

        <div className="space-y-3">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
            <span className="bg-gradient-to-r from-emerald-400 via-white to-purple-400 bg-clip-text text-transparent">
              AI Trading Hub
            </span>
          </h1>
          <p className="text-base text-muted-foreground max-w-md mx-auto leading-relaxed">
            AIトレーディングハブ — Platform trading berbasis kecerdasan buatan dengan sinyal real-time dan analitik canggih.
          </p>
        </div>

        {/* Feature badges */}
        <div className="flex flex-wrap justify-center gap-3">
          {[
            { icon: TrendingUp, label: "Real-time Signals", color: "text-trade-up" },
            { icon: Shield, label: "Secure API Keys", color: "text-primary" },
            { icon: Activity, label: "Neural Analytics", color: "text-chart-5" },
          ].map((feature) => (
            <div
              key={feature.label}
              className="flex items-center gap-2 px-4 py-2 rounded-full glass-panel text-xs font-medium"
            >
              <feature.icon className={`w-3.5 h-3.5 ${feature.color}`} />
              <span className="text-muted-foreground">{feature.label}</span>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link href="/login">
            <Button className="bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white font-semibold shadow-lg shadow-emerald-500/20 px-8 py-5 text-sm cursor-pointer">
              Login
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
          <Link href="/register">
            <Button
              variant="outline"
              className="border-white/10 hover:bg-white/5 px-8 py-5 text-sm cursor-pointer"
            >
              Register
            </Button>
          </Link>
        </div>

        <p className="text-[10px] text-muted-foreground/50 uppercase tracking-widest">
          Powered by Neural Engine v2 &mdash; ニューラルエンジン
        </p>
      </div>
    </div>
  );
}
