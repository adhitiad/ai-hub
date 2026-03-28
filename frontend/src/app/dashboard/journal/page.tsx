"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { journalService } from "@/services/api";
import type { TradeHistory, TradingStats } from "@/types";
import { cn } from "@/lib/utils";

// rechart components
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// shadcn/ui
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// FontAwesome
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faBook,
  faChartLine,
  faClockRotateLeft,
  faBullseye,
  faTrophy,
  faFileInvoiceDollar,
  faFire,
  faCircleNotch,
  faArrowTrendUp,
  faArrowTrendDown,
  faCalendarDays,
  faInbox,
} from "@fortawesome/free-solid-svg-icons";

export default function JournalPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [activeTab, setActiveTab] = useState<"history" | "stats">("stats");
  const [history, setHistory] = useState<TradeHistory[]>([]);
  const [stats, setStats] = useState<TradingStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await journalService.getHistory(100);
      setHistory(data);
    } catch {
      setError("Gagal memuat riwayat trading");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await journalService.getStats();
      setStats(data);
    } catch {
      setError("Gagal memuat statistik");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    if (activeTab === "stats") fetchStats();
    else fetchHistory();
  }, [activeTab, isAuthenticated, fetchStats, fetchHistory]);

  const COLORS_PIE = ["var(--trade-up)", "var(--trade-down)"];

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tight">
            Trading Journal
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            📓 Performance insights & trade history — <span className="text-chart-5 font-black uppercase tracking-widest text-[10px]">Elite Hub</span>
          </p>
        </div>

        <Tabs 
          value={activeTab} 
          onValueChange={(v) => setActiveTab(v as any)} 
          className="w-auto"
        >
          <TabsList className="glass-panel border-white/10 p-1">
            <TabsTrigger value="stats" className="gap-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer px-4">
               <FontAwesomeIcon icon={faChartLine as IconProp} className="w-3.5 h-3.5" />
               Statistik
            </TabsTrigger>
            <TabsTrigger value="history" className="gap-2 data-[state=active]:bg-primary/20 data-[state=active]:text-primary cursor-pointer px-4">
               <FontAwesomeIcon icon={faClockRotateLeft as IconProp} className="w-3.5 h-3.5" />
               Riwayat
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {error && (
        <Card className="border-trade-down/20 bg-trade-down/5">
           <CardContent className="py-4 text-trade-down text-sm font-bold flex items-center gap-2">
              <span className="text-xl">⚠️</span> {error}
           </CardContent>
        </Card>
      )}

      {loading ? (
        <div className="py-32 text-center">
          <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-8 h-8 text-primary mx-auto mb-4" />
          <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground animate-pulse">Computing stats...</p>
        </div>
      ) : activeTab === "stats" && stats ? (
        <div className="space-y-8 animate-in fade-in duration-500">
           {/* Top Stats Cards */}
           <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
             {[
                {
                  label: "Total Trades",
                  value: stats.total_trades,
                  icon: faBullseye,
                  color: "text-blue-400",
                  bg: "bg-blue-400/10",
                  border: "border-blue-400/20"
                },
                {
                  label: "Win Rate",
                  value: `${stats.win_rate?.toFixed(1)}%`,
                  icon: faTrophy,
                  color: (stats.win_rate || 0) >= 50 ? "text-trade-up" : "text-trade-down",
                  bg: (stats.win_rate || 0) >= 50 ? "bg-trade-up/10" : "bg-trade-down/10",
                  border: (stats.win_rate || 0) >= 50 ? "border-trade-up/20" : "border-trade-down/20"
                },
                {
                  label: "Net Profit/Loss",
                  value: `${stats.total_pnl >= 0 ? "+" : ""}${stats.total_pnl?.toLocaleString()}`,
                  icon: faFileInvoiceDollar,
                  color: stats.total_pnl >= 0 ? "text-trade-up" : "text-trade-down",
                  bg: stats.total_pnl >= 0 ? "bg-trade-up/10" : "bg-trade-down/10",
                   border: stats.total_pnl >= 0 ? "border-trade-up/20" : "border-trade-down/20"
                },
                {
                  label: "Profit Factor",
                  value: stats.profit_factor?.toFixed(2),
                  icon: faFire,
                  color: (stats.profit_factor || 0) >= 1 ? "text-chart-4" : "text-trade-down",
                  bg: "bg-chart-4/10",
                  border: "border-chart-4/20"
                },
             ].map((card) => (
                <Card key={card.label} className={cn("glass-panel border-white/10 overflow-hidden", card.border)}>
                   <CardContent className="p-6">
                      <div className="flex items-center justify-between mb-4">
                         <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center", card.bg)}>
                            <FontAwesomeIcon icon={card.icon as IconProp} className={cn("w-5 h-5", card.color)} />
                         </div>
                         <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">{card.label}</span>
                      </div>
                      <p className={cn("text-3xl font-black tracking-tighter", card.color)}>{card.value}</p>
                   </CardContent>
                </Card>
             ))}
           </div>

           {/* Metrics Grid */}
           <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "AVG WIN", value: `+${stats.avg_win?.toLocaleString()}`, color: "text-trade-up" },
                { label: "AVG LOSS", value: stats.avg_loss?.toLocaleString(), color: "text-trade-down" },
                { label: "BEST TRADE", value: `+${stats.best_trade?.toLocaleString()}`, color: "text-trade-up" },
                { label: "MAX DRAWDOWN", value: `${stats.max_drawdown?.toFixed(1)}%`, color: "text-trade-down" },
              ].map((item) => (
                <Card key={item.label} className="glass-panel border-white/10 py-4 px-6">
                  <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest mb-1">{item.label}</p>
                  <p className={cn("text-lg font-bold font-mono", item.color)}>{item.value}</p>
                </Card>
              ))}
           </div>

           {/* Charts Row */}
           <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Equity Curve */}
              <Card className="lg:col-span-8 glass-panel border-white/10">
                <CardHeader className="pb-2">
                   <div className="flex items-center gap-2">
                      <FontAwesomeIcon icon={faArrowTrendUp as IconProp} className="w-4 h-4 text-primary" />
                      <CardTitle className="text-sm font-black uppercase tracking-widest">Equity Growth</CardTitle>
                   </div>
                </CardHeader>
                <CardContent className="h-[350px] pt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={(stats.equity_curve || []).map((v, i) => ({ idx: i + 1, equity: v }))}
                    >
                      <defs>
                        <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--trade-up)" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="var(--trade-up)" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" vertical={false} />
                      <XAxis 
                        dataKey="idx" 
                        stroke="rgba(255,255,255,0.1)"
                        tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} 
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis 
                         stroke="rgba(255,255,255,0.1)"
                         tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} 
                         axisLine={false}
                         tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(10,10,10,0.95)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "12px",
                          fontSize: "12px",
                          backdropFilter: "blur(10px)",
                          boxShadow: "0 10px 30px -10px rgba(0,0,0,0.5)"
                        }}
                      />
                      <Area type="monotone" dataKey="equity" stroke="var(--trade-up)" fill="url(#eqGrad)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Composition */}
              <Card className="lg:col-span-4 glass-panel border-white/10">
                <CardHeader className="pb-2 text-center">
                   <CardTitle className="text-sm font-black uppercase tracking-widest">Performance Mix</CardTitle>
                </CardHeader>
                <CardContent className="h-[300px] flex flex-col justify-center items-center">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: "Win", value: stats.win_rate || 0 },
                          { name: "Loss", value: 100 - (stats.win_rate || 0) },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        dataKey="value"
                        strokeWidth={4}
                        stroke="rgba(0,0,0,0.2)"
                      >
                        {COLORS_PIE.map((c, i) => (
                          <Cell key={i} fill={c} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          background: "rgba(0,0,0,0.9)",
                          border: "none",
                          borderRadius: "8px",
                          fontSize: "12px",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-4">
                    <div className="flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-trade-up" />
                       <span className="text-[10px] font-black uppercase text-trade-up">Win {stats.win_rate?.toFixed(1)}%</span>
                    </div>
                    <div className="flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-trade-down" />
                       <span className="text-[10px] font-black uppercase text-trade-down">Loss {(100 - (stats.win_rate || 0)).toFixed(1)}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
           </div>
        </div>
      ) : activeTab === "history" ? (
        /* History Table Container */
        <Card className="glass-panel border-white/10 overflow-hidden animate-in fade-in duration-500">
          <CardHeader className="bg-white/5 border-b border-white/10 py-4 px-6">
            <div className="flex items-center justify-between">
               <div className="flex items-center gap-3">
                  <FontAwesomeIcon icon={faInbox as IconProp} className="w-4 h-4 text-primary" />
                  <CardTitle className="text-sm font-black uppercase tracking-widest">Order Execution Log</CardTitle>
               </div>
               <Badge variant="outline" className="border-white/10 text-muted-foreground font-mono">
                  {history.length} RECORDS
               </Badge>
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-black/20">
                <TableRow className="hover:bg-transparent border-white/10">
                  <TableHead className="font-black text-[10px] uppercase tracking-widest px-6 whitespace-nowrap">Asset</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-center whitespace-nowrap">Side</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-right whitespace-nowrap">Entry</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-right whitespace-nowrap">Exit</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-right whitespace-nowrap">Qty</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-right whitespace-nowrap">Realized P&L</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-right whitespace-nowrap">%</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest text-center whitespace-nowrap">Status</TableHead>
                  <TableHead className="font-black text-[10px] uppercase tracking-widest px-6 whitespace-nowrap">Execution Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.map((t, i) => {
                  const pnl = t.pnl ?? 0;
                  return (
                    <TableRow
                      key={t.id || t._id || i}
                      className="border-white/5 hover:bg-white/5 transition-all group"
                    >
                      <TableCell className="px-6 py-4">
                         <div className="flex flex-col">
                            <span className="font-bold text-sm tracking-tight">{t.symbol}</span>
                            <span className="text-[9px] font-black uppercase text-muted-foreground opacity-50">Executed</span>
                         </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge className={cn(
                           "font-black text-[10px] px-2 py-0.5 border-none",
                           t.action === "BUY" ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                        )}>
                           {t.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm font-bold">{t.entry_price?.toLocaleString()}</TableCell>
                      <TableCell className="text-right font-mono text-sm">{t.exit_price?.toLocaleString() ?? "—"}</TableCell>
                      <TableCell className="text-right font-mono text-sm">{t.quantity}</TableCell>
                      <TableCell className={cn("text-right font-mono font-black text-sm", pnl >= 0 ? "text-trade-up" : "text-trade-down")}>
                        {pnl >= 0 ? "+" : ""}{pnl.toLocaleString()}
                      </TableCell>
                      <TableCell className={cn("text-right font-mono text-[10px] font-black", pnl >= 0 ? "text-trade-up" : "text-trade-down")}>
                        {t.pnl_percent != null ? `${t.pnl_percent.toFixed(1)}%` : "—"}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className={cn(
                          "w-16 justify-center border-none font-black text-[9px] uppercase",
                          t.status === "CLOSED" ? "bg-white/5 text-muted-foreground"
                          : t.status === "OPEN" ? "bg-trade-up/10 text-trade-up"
                          : "bg-chart-4/10 text-chart-4"
                        )}>
                          {t.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="px-6 text-[11px] font-bold text-muted-foreground">
                        <div className="flex items-center gap-2">
                           <FontAwesomeIcon icon={faCalendarDays as IconProp} className="w-3 h-3 opacity-30" />
                           {t.entry_date ? new Date(t.entry_date).toLocaleDateString("id-ID") : "—"}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
                {history.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} className="h-48 text-center text-muted-foreground italic font-medium">
                      No matching records in the vault.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      ) : (
        <div className="py-32 text-center opacity-30">
          <FontAwesomeIcon icon={faBook as IconProp} className="w-16 h-16 mb-4" />
          <p className="text-lg font-black uppercase tracking-widest">Journal Empty</p>
        </div>
      )}
    </div>
  );
}
