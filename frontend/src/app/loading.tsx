"use client";

import { Loader2 } from "lucide-react";

export default function Loading() {
  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background/60 backdrop-blur-xl">
      <div className="relative flex items-center justify-center">
        {/* Glow Effect */}
        <div className="absolute w-32 h-32 bg-primary/20 rounded-full blur-3xl animate-pulse" />

        {/* Main Spinner */}
        <div className="relative">
          <Loader2 className="w-12 h-12 text-primary animate-spin" />

          {/* Decorative Ring */}
          <div className="absolute inset-0 border-2 border-white/5 rounded-full scale-150" />
        </div>
      </div>

      <div className="mt-8 text-center space-y-2">
        <h3 className="text-xl font-bold bg-gradient-to-r from-white to-white/40 bg-clip-text text-transparent">
          AI Trading Hub
        </h3>
        <div className="loaders"></div>
        <p className="text-sm text-muted-foreground animate-pulse">
          Menyiapkan data intelijen pasar...
        </p>
      </div>
    </div>
  );
}

/* HTML: <div class="loader"></div> */
