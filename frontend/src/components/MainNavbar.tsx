"use client";

import { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/theme-toggle";
import { systemService } from "@/services/api";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSearch } from "@fortawesome/free-solid-svg-icons";
import { IconProp } from "@fortawesome/fontawesome-svg-core";
import { cn } from "@/lib/utils";

export function MainNavbar() {
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Standard approach to handle hydration in React.
    // Wrap state update with a check or delay to satisfy strict linting.
    const timer = setTimeout(() => setMounted(true), 0);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await systemService.healthCheck();
        setIsOnline(true);
      } catch (err) {
        console.error("Health check failed:", err);
        setIsOnline(false);
      }
    };
    
    checkHealth();
    // Poll health every 60 seconds
    const interval = setInterval(checkHealth, 60000);
    return () => clearInterval(interval);
  }, []);

  if (!mounted) return null;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border/50 bg-background/60 backdrop-blur-xl supports-[backdrop-filter]:bg-background/40">
      <div className="container flex h-16 max-w-screen-2xl items-center justify-between px-8">
        <div className="flex items-center gap-4 flex-1">
          {/* Dashboard Left Tag */}
          <div className="flex items-center gap-2 pr-4 border-r border-border/50">
            <span className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.3em] font-mono">
              AI ENGINE
            </span>
            <span className="px-1.5 py-0.5 rounded text-[8px] bg-emerald-500/10 text-emerald-500 font-bold border border-emerald-500/20">
              STABLE
            </span>
          </div>

          {/* Search Bar */}
          <div className="relative w-full max-w-md ml-4 group">
            <FontAwesomeIcon 
              icon={faSearch as IconProp} 
              className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-primary transition-colors" 
            />
            <Input
              type="search"
              placeholder="Search assets, signals, orders..."
              className="w-full bg-white/5 border-border/50 pl-10 h-9 text-sm focus-visible:ring-primary/30 transition-all rounded-xl"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Health Indicator */}
          <div className="flex items-center gap-2 group cursor-help">
            <div className="relative flex h-2 w-2">
              <span className={cn(
                "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
                isOnline === true ? "bg-emerald-400" : isOnline === false ? "bg-red-400" : "bg-slate-400"
              )}></span>
              <span className={cn(
                "relative inline-flex rounded-full h-2 w-2 transition-colors duration-500",
                isOnline === true ? "bg-emerald-500" : isOnline === false ? "bg-red-500" : "bg-slate-500"
              )}></span>
            </div>
            <div className="flex flex-col">
              <span className="text-[8px] font-black uppercase tracking-widest text-muted-foreground leading-tight">
                Backend Status
              </span>
              <span className={cn(
                "text-[9px] font-bold uppercase tracking-tighter leading-tight",
                isOnline === true ? "text-emerald-500" : isOnline === false ? "text-red-500" : "text-slate-500"
              )}>
                {isOnline === true ? "ONLINE" : isOnline === false ? "OFFLINE" : "CHECKING..."}
              </span>
            </div>
            
            {/* Popover/Tooltip effect on hover could go here */}
          </div>

          <Separator orientation="vertical" className="h-4 bg-border/50 mx-2" />

          {/* Theme Toggle */}
          <ThemeToggle />
          
          <Separator orientation="vertical" className="h-4 bg-border/50 mx-2" />
          
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-purple-500 flex items-center justify-center text-[10px] font-black p-[1px] shadow-lg shadow-primary/20">
                <div className="w-full h-full bg-background rounded-full flex items-center justify-center">
                    U
                </div>
             </div>
          </div>
        </div>
      </div>
    </header>
  );
}
