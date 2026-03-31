"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCcw, Home } from "lucide-react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Audit error ke console untuk debugging
    console.error("🔥 Global Error Caught:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-background">
      <div className="w-full max-w-md text-center space-y-8 animate-in zoom-in duration-500">
        {/* Error Icon */}
        <div className="mx-auto w-20 h-20 rounded-3xl bg-trade-down/10 flex items-center justify-center ring-1 ring-trade-down/30">
          <AlertCircle className="w-10 h-10 text-trade-down" />
        </div>

        {/* Text Content */}
        <div className="space-y-3">
          <h1 className="text-3xl font-bold tracking-tight">System Crash</h1>
          <p className="text-muted-foreground text-sm max-w-[320px] mx-auto leading-relaxed">
            Terjadi kesalahan fatal saat memuat antarmuka. Kami telah mencatat masalah ini untuk diperbaiki.
          </p>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10 mt-6 font-mono text-[10px] text-trade-down text-left overflow-hidden">
            <span className="opacity-40">ERROR_ID:</span> {error.digest || "RUNTIME_EXCEPTION"}
            <br />
            <span className="opacity-40">REASON:</span> {error.message.substring(0, 100)}...
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button
            onClick={() => reset()}
            className="w-full sm:w-auto bg-primary text-black font-semibold min-w-[140px]"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Coba Lagi
          </Button>
          <Link href="/dashboard" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full border-white/10 hover:bg-white/5 min-w-[140px]">
              <Home className="w-4 h-4 mr-2" />
              Ke Dashboard
            </Button>
          </Link>
        </div>

        <p className="text-[10px] text-muted-foreground opacity-30">
          AI Hub Version 2.4.0 • System Secure
        </p>
      </div>
    </div>
  );
}
