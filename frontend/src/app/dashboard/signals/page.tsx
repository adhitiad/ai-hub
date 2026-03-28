"use client";

import EmptyState from "@/components/EmptyState";
import SignalCard from "@/components/SignalCard";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { signalService } from "@/services/api";
import { SignalStats, TradingSignal } from "@/types";
import { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faAngleLeft,
  faAngleRight,
  faArrowsRotate,
  faBolt,
  faClockRotateLeft,
  faRobot,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useCallback, useEffect, useState } from "react";

export default function SignalsPage() {
  const [activeTab, setActiveTab] = useState<"active" | "expired">("active");
  const [signals, setSignals] = useState<TradingSignal[]>([]);
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(10);
  const [total, setTotal] = useState(0);

  const fetchSignals = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      try {
        const [res, statsRes] = await Promise.all([
          signalService.list({ status: activeTab, page, limit }),
          signalService.getStats(),
        ]);

        let data = res.data.data;

        // Filter active signals to 3 hours as requested
        if (activeTab === "active") {
          const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60 * 1000);
          data = data.filter((sig) => {
            const created = sig.created_at
              ? new Date(sig.created_at)
              : new Date();
            return created >= threeHoursAgo;
          });
        }

        setSignals(data);
        setTotal(res.data.total);
        setStats(statsRes.data);
      } catch (err) {
        console.error("Failed to fetch signals:", err);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeTab, page, limit],
  );

  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-8 pb-12 animate-in fade-in duration-700">
      {/* Dynamic Header with Stats */}
      <div className="relative overflow-hidden rounded-3xl border border-border/50 bg-gradient-to-br from-primary/10 via-background to-chart-5/10 p-8 shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] -z-10" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-chart-5/5 blur-[100px] -z-10" />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-widest">
              <FontAwesomeIcon icon={faRobot as IconProp} className="w-3 h-3" />
              Neural Signal Protocol v4.0
            </div>
            <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-foreground leading-[0.9]">
              ALGORITHMIC <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-emerald-400 to-chart-5">
                TRADING SIGNALS
              </span>
            </h1>
            <p className="text-muted-foreground text-sm max-w-md leading-relaxed font-medium">
              Sistem deteksi anomali pasar menggunakan Neural Network dan
              Analisis Bandarmologi Real-Time. Konfirmasi teknikal setiap 15
              menit.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4 backdrop-blur-md bg-card/30 p-6 rounded-2xl border border-border/50 relative overflow-hidden group">
            <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="space-y-1 relative z-10">
              <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-black">
                Accuracy Score
              </p>
              <div className="flex items-baseline gap-1">
                <span className="text-6xl font-black text-primary drop-shadow-[0_0_15px_var(--primary)]">
                  {stats?.win_rate ?? 0}%
                </span>
              </div>
              <p className="text-[9px] text-primary/50 font-bold uppercase tracking-widest">
                Master Protocol Active
              </p>
            </div>
            <div className="space-y-1 text-right relative z-10">
              <p className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] font-black">
                Total Analysed
              </p>
              <div className="flex items-baseline justify-end gap-1">
                <span className="text-4xl font-black text-foreground/90">
                  {stats?.total_signals ?? 0}
                </span>
                <span className="text-[10px] text-muted-foreground/40 font-bold uppercase tracking-widest font-mono">
                  Hits
                </span>
              </div>
            </div>
            <div className="col-span-2 pt-4 border-t border-border/50 space-y-3 relative z-10">
              <div className="flex justify-between items-center text-[9px] text-muted-foreground font-black uppercase tracking-widest">
                <div className="flex gap-4">
                  <span className="flex items-center gap-1.5 text-emerald-500">
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                    P: {stats?.wins ?? 0}
                  </span>
                  <span className="flex items-center gap-1.5 text-destructive">
                    <div className="w-1.5 h-1.5 bg-destructive rounded-full" />
                    L: {stats?.losses ?? 0}
                  </span>
                </div>
                <span className="text-muted-foreground/30 italic">
                  Global Engine Stats
                </span>
              </div>
              <div className="w-full h-1.5 bg-muted/30 rounded-full overflow-hidden border border-border/5">
                <div
                  className="h-full bg-gradient-to-r from-emerald-600 via-primary to-chart-5 transition-all duration-1000 shadow-[0_0_10px_var(--primary)]"
                  style={{ width: `${stats?.win_rate ?? 0}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <Tabs
          defaultValue="active"
          onValueChange={(v) => {
            setActiveTab(v as "active" | "expired");
            setPage(1);
          }}
          className="w-full"
        >
          <div className="flex flex-col md:flex-row items-center justify-between gap-4 mb-8">
            <div className="flex items-center gap-3 w-full md:w-auto">
              <TabsList className="bg-muted/50 border border-border/50 p-1 rounded-xl h-11">
                <TabsTrigger
                  value="active"
                  className="flex items-center gap-2 px-6 rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all duration-300 font-black uppercase text-[10px] tracking-widest"
                >
                  <FontAwesomeIcon
                    icon={faBolt as IconProp}
                    className="w-3 h-3"
                  />
                  Live Signals
                  <span className="ml-1 opacity-60 font-mono">
                    [{activeTab === "active" ? total : "-"}]
                  </span>
                </TabsTrigger>
                <TabsTrigger
                  value="expired"
                  className="flex items-center gap-2 px-6 rounded-lg data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all duration-300 font-black uppercase text-[10px] tracking-widest"
                >
                  <FontAwesomeIcon
                    icon={faClockRotateLeft as IconProp}
                    className="w-3 h-3"
                  />
                  Historical
                  <span className="ml-1 opacity-60 font-mono">
                    [{activeTab === "expired" ? total : "-"}]
                  </span>
                </TabsTrigger>
              </TabsList>

              <Button
                variant="outline"
                size="icon"
                onClick={() => fetchSignals(true)}
                disabled={refreshing || loading}
                className="w-11 h-11 rounded-xl border-border/50 hover:bg-muted/50 transition-all"
              >
                <FontAwesomeIcon
                  icon={faArrowsRotate as IconProp}
                  className={cn(
                    "w-3.5 h-3.5 text-muted-foreground",
                    refreshing && "animate-spin",
                  )}
                />
              </Button>
            </div>

            <div className="flex items-center gap-4 w-full md:w-auto self-end">
              <div className="flex items-center gap-3 bg-muted/30 border border-border/50 px-4 py-2 rounded-xl h-11">
                <span className="text-[10px] text-muted-foreground font-black tracking-widest">
                  CAPACITY:
                </span>
                <Select
                  value={limit.toString()}
                  onValueChange={(v) => {
                    setLimit(parseInt(v));
                    setPage(1);
                  }}
                >
                  <SelectTrigger className="w-[100px] h-7 bg-transparent border-0 focus:ring-0 text-xs font-black shadow-none p-0 uppercase tracking-tighter">
                    <SelectValue placeholder="10" />
                  </SelectTrigger>
                  <SelectContent className="border-border/50 bg-background/95 backdrop-blur-xl">
                    <SelectItem
                      value="5"
                      className="text-xs font-bold uppercase"
                    >
                      5 / Segment
                    </SelectItem>
                    <SelectItem
                      value="10"
                      className="text-xs font-bold uppercase"
                    >
                      10 / Segment
                    </SelectItem>
                    <SelectItem
                      value="25"
                      className="text-xs font-bold uppercase"
                    >
                      25 / Segment
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <TabsContent
            value="active"
            className="mt-0 focus-visible:outline-none"
          >
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="h-72 rounded-3xl border border-border/20 bg-muted/10 animate-pulse"
                  />
                ))}
              </div>
            ) : signals.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-6">
                {signals.map((sig) => (
                  <SignalCard key={sig.id} signal={sig} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={
                  <FontAwesomeIcon
                    icon={faTriangleExclamation as IconProp}
                    className="w-16 h-16 text-primary/10 mb-8"
                  />
                }
                message="No active sequences detected in the last 3-hour window."
              />
            )}
          </TabsContent>

          <TabsContent
            value="expired"
            className="mt-0 focus-visible:outline-none"
          >
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div
                    key={i}
                    className="h-72 rounded-3xl border border-border/20 bg-muted/10 animate-pulse"
                  />
                ))}
              </div>
            ) : signals.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-6">
                {signals.map((sig) => (
                  <SignalCard key={sig.id} signal={sig} />
                ))}
              </div>
            ) : (
              <EmptyState
                icon={
                  <FontAwesomeIcon
                    icon={faClockRotateLeft as IconProp}
                    className="w-16 h-16 text-muted-foreground/10 mb-8"
                  />
                }
                message="Archive is currently empty. No historical data found."
              />
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Modern Pagination */}
      {totalPages > 1 && (
        <div className="flex flex-col items-center gap-4 pt-12 border-t border-border/50">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              className="w-12 h-12 rounded-2xl border-border/50 bg-muted/30 hover:bg-muted/50 transition-all text-foreground disabled:opacity-20"
            >
              <FontAwesomeIcon
                icon={faAngleLeft as IconProp}
                className="w-4 h-4"
              />
            </Button>

            <div className="flex items-center bg-muted/30 border border-border/50 rounded-2xl px-8 h-12">
              <span className="text-2xl font-black text-primary font-mono">
                {page}
              </span>
              <span className="mx-3 text-muted-foreground/20 font-light">
                /
              </span>
              <span className="text-sm font-black text-muted-foreground font-mono">
                {totalPages}
              </span>
            </div>

            <Button
              variant="outline"
              size="icon"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="w-12 h-12 rounded-2xl border-border/50 bg-muted/30 hover:bg-muted/50 transition-all text-foreground disabled:opacity-20"
            >
              <FontAwesomeIcon
                icon={faAngleRight as IconProp}
                className="w-4 h-4"
              />
            </Button>
          </div>
          <p className="text-[10px] text-muted-foreground uppercase tracking-[0.4em] font-black">
            Segment Index Controller
          </p>
        </div>
      )}
    </div>
  );
}
