"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { screenerService } from "@/services/api";
import { useAuthStore } from "@/stores/useAuthStore";
import type { SignalItem } from "@/types";
import { cn } from "@/lib/utils";

// shadcn/ui
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
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

// FontAwesome
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faFilter,
  faSliders,
  faCircleNotch,
  faRotateRight,
  faArrowTrendUp,
  faArrowTrendDown,
  faMinus,
  faMagnifyingGlass,
  faEye,
} from "@fortawesome/free-solid-svg-icons";

export default function ScreenerPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [results, setResults] = useState<SignalItem[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [signalOnly, setSignalOnly] = useState(false);
  const [bandarAccum, setBandarAccum] = useState(false);
  const [rsiMin, setRsiMin] = useState(0);
  const [rsiMax, setRsiMax] = useState(100);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) router.push("/login");
  }, [isAuthenticated, router]);

  const runScreener = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await screenerService.run({
        signal_only: signalOnly,
        bandar_accum: bandarAccum,
        rsi_min: rsiMin,
        rsi_max: rsiMax,
      });
      setResults(data.matches || []);
      setCount(data.count || 0);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Gagal menjalankan screener";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) runScreener();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const getActionBadge = (action?: string) => {
    const a = (action || "HOLD").toUpperCase();
    if (a === "BUY" || a === "STRONG BUY")
      return (
        <Badge className="bg-trade-up/15 text-trade-up border-trade-up/20 hover:bg-trade-up/20 gap-1.5 px-2.5 py-1">
          <FontAwesomeIcon icon={faArrowTrendUp as IconProp} className="w-3 h-3" /> {a}
        </Badge>
      );
    if (a === "SELL" || a === "STRONG SELL")
      return (
        <Badge className="bg-trade-down/15 text-trade-down border-trade-down/20 hover:bg-trade-down/20 gap-1.5 px-2.5 py-1">
          <FontAwesomeIcon icon={faArrowTrendDown as IconProp} className="w-3 h-3" /> {a}
        </Badge>
      );
    return (
      <Badge variant="outline" className="border-white/10 text-muted-foreground gap-1.5 px-2.5 py-1">
        <FontAwesomeIcon icon={faMinus as IconProp} className="w-3 h-3" /> {a}
      </Badge>
    );
  };

  if (!isAuthenticated) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tight">
            Stock Screener
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            🔍 Filter assets with AI signals — <span className="text-chart-5 font-black uppercase tracking-widest text-[10px]">Elite Analysis</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "glass-panel border-white/10 hover:border-white/20 transition-all gap-2",
              showFilters && "bg-primary/20 text-primary border-primary/30"
            )}
          >
            <FontAwesomeIcon icon={faSliders as IconProp} className="w-3.5 h-3.5" />
            Scanner Options
          </Button>
          
          <Button
            onClick={runScreener}
            disabled={loading}
            className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 font-black tracking-wider gap-2 px-6"
          >
             {loading ? (
              <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-3.5 h-3.5" />
            ) : (
              <FontAwesomeIcon icon={faRotateRight as IconProp} className="w-3.5 h-3.5" />
            )}
            RUN SCAN
          </Button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card className="glass-panel border-white/10 overflow-hidden animate-in fade-in slide-in-from-top-4 duration-300">
          <CardHeader className="pb-4">
             <CardTitle className="text-sm font-black uppercase tracking-widest text-primary flex items-center gap-2">
                <FontAwesomeIcon icon={faFilter as IconProp} className="w-3.5 h-3.5" />
                Scan Parameters
             </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="signalOnly" 
                    checked={signalOnly} 
                    onCheckedChange={(checked) => setSignalOnly(!!checked)}
                  />
                  <Label htmlFor="signalOnly" className="text-sm font-bold cursor-pointer">Signal Only (BUY/SELL)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id="bandarAccum" 
                    checked={bandarAccum} 
                    onCheckedChange={(checked) => setBandarAccum(!!checked)}
                  />
                  <Label htmlFor="bandarAccum" className="text-sm font-bold cursor-pointer">Bandar Akumulasi</Label>
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">RSI Min Threshold</Label>
                <Input
                  type="number"
                  value={rsiMin}
                  onChange={(e) => setRsiMin(Number(e.target.value))}
                  className="bg-white/5 border-white/10 h-10 font-mono"
                  min={0}
                  max={100}
                />
              </div>

              <div className="space-y-3">
                <Label className="text-[10px] font-black uppercase tracking-widest text-muted-foreground">RSI Max Threshold</Label>
                <Input
                  type="number"
                  value={rsiMax}
                  onChange={(e) => setRsiMax(Number(e.target.value))}
                  className="bg-white/5 border-white/10 h-10 font-mono"
                  min={0}
                  max={100}
                />
              </div>

              <div className="flex items-end">
                <p className="text-[10px] text-muted-foreground italic leading-tight">
                  Adjust these parameters to find high-probability setups across multiple timeframe analysis.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Area */}
      <Card className="glass-panel border-white/10 overflow-hidden">
        <CardHeader className="border-b border-white/5 bg-white/5 flex flex-row items-center justify-between pb-3">
           <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
                 <FontAwesomeIcon icon={faMagnifyingGlass as IconProp} className="w-3.5 h-3.5" />
              </div>
              <div>
                 <CardTitle className="text-lg font-black uppercase tracking-tight">Active Scan results</CardTitle>
                 <CardDescription className="text-[10px]">
                    Found <span className="text-primary font-bold">{count}</span> matched assets based on criteria
                 </CardDescription>
              </div>
           </div>
        </CardHeader>
        <CardContent className="p-0">
          {error ? (
            <div className="py-20 text-center space-y-4">
               <div className="w-12 h-12 rounded-full border border-trade-down/20 bg-trade-down/10 flex items-center justify-center mx-auto text-trade-down">
                  <FontAwesomeIcon icon={faMinus as IconProp} className="w-4 h-4" />
               </div>
               <p className="text-sm text-trade-down font-bold">{error}</p>
               <Button variant="outline" onClick={runScreener} className="border-white/10">Try Again</Button>
            </div>
          ) : loading ? (
            <div className="py-24 text-center">
              <FontAwesomeIcon icon={faCircleNotch as IconProp} spin className="w-8 h-8 text-primary mx-auto mb-4" />
              <p className="text-xs font-black uppercase tracking-[0.2em] text-muted-foreground">Analyzing Markets...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-white/5">
                  <TableRow className="hover:bg-transparent border-white/10">
                    <TableHead className="font-black text-[10px] uppercase tracking-widest w-[150px]">Symbol</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-center">Action</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-right">Confidence</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-right">Price</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-right">Target (TP)</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-right">Defensive (SL)</TableHead>
                    <TableHead className="font-black text-[10px] uppercase tracking-widest text-center">Charts</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results?.map((item, i) => (
                    <TableRow 
                      key={`${item.symbol}-${i}`}
                      className="group border-white/5 hover:bg-white/5 transition-all cursor-pointer"
                      onClick={() => router.push(`/dashboard/market?symbol=${item.symbol}`)}
                    >
                      <TableCell className="font-bold py-4">
                        <div className="flex flex-col">
                           <span className="text-sm tracking-tight">{item.symbol}</span>
                           <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-black">Elite Hub</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {getActionBadge(item.Action)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={cn(
                          "px-2 py-1 rounded text-xs font-mono font-bold border",
                          item.Confidence && (item.Confidence as number) > 70 
                            ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" 
                            : "bg-white/5 text-muted-foreground border-white/10"
                        )}>
                          {item.Confidence != null ? `${(item.Confidence as number).toFixed(1)}%` : "—"}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono font-bold text-sm">
                        {item.Price?.toLocaleString() ?? "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm text-trade-up font-bold">
                        {(item as any).TP ? Number((item as any).TP).toLocaleString() : "—"}
                      </TableCell>
                      <TableCell className="text-right font-mono text-sm text-trade-down font-bold">
                        {(item as any).SL ? Number((item as any).SL).toLocaleString() : "—"}
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="w-8 h-8 rounded-lg border border-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-white/5 text-primary">
                           <FontAwesomeIcon icon={faEye as IconProp} className="w-3.5 h-3.5" />
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                  {results.length === 0 && !loading && (
                    <TableRow>
                      <TableCell colSpan={7} className="h-48 text-center">
                        <div className="flex flex-col items-center justify-center space-y-2 opacity-40">
                           <FontAwesomeIcon icon={faFilter as IconProp} className="w-8 h-8 mb-2" />
                           <p className="text-sm font-bold">No assets matched your criteria.</p>
                           <p className="text-xs">Try loosening your scan parameters.</p>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
