"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useSimulationSocket } from "@/hooks/useSimulationSocket";
import { useSymbols } from "@/hooks/useSymbols";
import { cn } from "@/lib/utils";
import { useState } from "react";

// rechart components
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// shadcn/ui
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";

// FontAwesome
import type { IconProp } from "@fortawesome/fontawesome-svg-core";
import {
  faChartLine,
  faClockRotateLeft,
  faForwardStep,
  faMicrochip,
  faPlay,
  faStop,
  faTimeline,
  faTriangleExclamation,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

export default function SimulationPage() {
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const { grouped: symbolGroups, loading: symbolsLoading } = useSymbols();

  const [activeSim, setActiveSim] = useState<{
    symbol: string;
    date: string;
  } | null>(null);

  const { data, isConnected, isFinished, error, connect, disconnect } =
    useSimulationSocket(activeSim?.symbol || "", activeSim?.date || "", false);

  const handleStart = () => {
    setActiveSim({ symbol, date });
    setTimeout(() => {
      connect();
    }, 100);
  };

  const handleStop = () => {
    disconnect();
    setActiveSim(null);
  };

  const currentPrice = data.length > 0 ? data[data.length - 1].close : 0;
  const previousPrice = data.length > 1 ? data[data.length - 2].close : 0;
  const isUp = currentPrice >= previousPrice;

  return (
    <div className="space-y-8 pb-12">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent uppercase tracking-tight">
            Time-Travel Simulation
          </h1>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            ⚡ Replay historical market conditions via{" "}
            <span className="text-chart-5 font-black uppercase tracking-widest text-[10px]">
              Neural Engine
            </span>
          </p>
        </div>

        {/* Controls Panel */}
        <div className="flex flex-wrap items-end gap-3 p-1 bg-white/5 border border-white/10 rounded-2xl">
          <div className="px-3 py-1 space-y-1">
            <Label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground opacity-50">
              Symbol
            </Label>
            <div className="relative group min-w-[160px]">
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                disabled={isConnected || symbolsLoading}
                className="w-full h-9 bg-transparent text-sm font-bold outline-none cursor-pointer appearance-none disabled:opacity-50"
              >
                {symbolsLoading ? (
                  <option>Loading...</option>
                ) : (
                  symbolGroups.map((group) => (
                    <optgroup
                      key={group.group}
                      label={group.group}
                      className="bg-black text-muted-foreground"
                    >
                      {group.options.map((opt) => (
                        <option
                          key={opt.value}
                          value={opt.value}
                          className="bg-black/90 text-foreground"
                        >
                          {opt.flag} {opt.value}
                        </option>
                      ))}
                    </optgroup>
                  ))
                )}
              </select>
            </div>
          </div>

          <div className="w-px h-8 bg-white/10 self-center" />

          <div className="px-3 py-1 space-y-1">
            <Label className="text-[9px] font-black uppercase tracking-widest text-muted-foreground opacity-50">
              Base Date
            </Label>
            <Input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              disabled={isConnected}
              className="h-8 border-none bg-transparent shadow-none font-bold text-sm p-0 focus-visible:ring-0 w-32"
            />
          </div>

          {isConnected ? (
            <Button
              onClick={handleStop}
              className="h-10 px-6 rounded-xl bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 font-black tracking-widest text-[10px] m-1"
            >
              <FontAwesomeIcon
                icon={faStop as IconProp}
                className="mr-2 w-3 h-3"
              />
              TERMINATE
            </Button>
          ) : (
            <Button
              onClick={handleStart}
              disabled={symbolsLoading}
              className="h-10 px-6 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 font-black tracking-widest text-[10px] m-1"
            >
              <FontAwesomeIcon
                icon={faPlay as IconProp}
                className="mr-2 w-3 h-3"
              />
              PLAY SESSION
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Card className="border-red-500/20 bg-red-500/5 animate-in slide-in-from-top-2">
          <CardContent className="py-4 text-red-400 text-xs font-bold flex items-center gap-3">
            <FontAwesomeIcon
              icon={faTriangleExclamation as IconProp}
              className="w-4 h-4"
            />
            <p className="tracking-tight uppercase">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Main Simulation Board */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Replay Chart Container */}
        <Card className="lg:col-span-9 glass-panel border-white/10 overflow-hidden relative min-h-[550px] flex flex-col">
          <div className="absolute top-0 right-0 p-48 bg-purple-500/5 blur-[120px] rounded-full pointer-events-none" />

          <CardHeader className="bg-white/5 border-b border-white/5 py-5 px-8 flex flex-row items-center justify-between relative z-10">
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 rounded-full bg-purple-400/20 flex items-center justify-center p-0.5">
                <div
                  className={cn(
                    "w-full h-full rounded-full",
                    isConnected
                      ? "bg-emerald-400 animate-pulse"
                      : "bg-purple-400/50",
                  )}
                />
              </div>
              <div>
                <CardTitle className="text-sm font-black uppercase tracking-widest flex items-center gap-3">
                  <FontAwesomeIcon
                    icon={faTimeline as IconProp}
                    className="w-3.5 h-3.5 opacity-30"
                  />
                  Neural Replay Core
                </CardTitle>
                <CardDescription className="text-[10px] font-black uppercase tracking-tighter opacity-50">
                  Synchronized WebSocket Stream
                </CardDescription>
              </div>
            </div>

            <div className="text-right">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground mb-1">
                {activeSim?.symbol || symbol}
              </p>
              <div className="flex items-center gap-3 justify-end">
                <span
                  className={cn(
                    "text-2xl font-black font-mono tracking-tighter transition-all duration-300",
                    isUp
                      ? "text-emerald-400 drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]"
                      : "text-red-400 drop-shadow-[0_0_8px_rgba(239,68,68,0.3)]",
                  )}
                >
                  {currentPrice.toFixed(2)}
                </span>
                {isFinished && (
                  <Badge className="bg-white/10 text-white border-white/10 text-[9px] font-black">
                    FINISHED
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 p-8 relative z-10 flex flex-col">
            {data.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center opacity-10">
                <FontAwesomeIcon
                  icon={faClockRotateLeft as IconProp}
                  className="w-24 h-24 mb-6"
                />
                <p className="font-black uppercase tracking-[0.4em] text-sm">
                  Awaiting Engine Init
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <LineChart
                  data={data}
                  margin={{ top: 20, right: 30, left: 10, bottom: 20 }}
                >
                  <defs>
                    <filter
                      id="glow"
                      x="-20%"
                      y="-20%"
                      width="140%"
                      height="140%"
                    >
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feComposite
                        in="SourceGraphic"
                        in2="blur"
                        operator="over"
                      />
                    </filter>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.03)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="time"
                    stroke="rgba(255,255,255,0.1)"
                    tick={{
                      fill: "rgba(255,255,255,0.3)",
                      fontSize: 10,
                      fontWeight: 700,
                    }}
                    tickFormatter={(val) => {
                      const d = new Date(val);
                      return `${d.getHours()}:${d.getMinutes().toString().padStart(2, "0")}`;
                    }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    stroke="rgba(255,255,255,0.1)"
                    tick={{
                      fill: "rgba(255,255,255,0.3)",
                      fontSize: 10,
                      fontWeight: 700,
                    }}
                    tickFormatter={(val) => val.toLocaleString()}
                    orientation="right"
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "rgba(10,10,10,0.95)",
                      border: "1px solid rgba(255,255,255,0.1)",
                      borderRadius: "12px",
                      fontSize: "12px",
                      backdropFilter: "blur(10px)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="var(--trade-up)"
                    strokeWidth={3}
                    dot={false}
                    isAnimationActive={false}
                    filter="url(#glow)"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Sidebar Info Section */}
        <div className="lg:col-span-3 space-y-6">
          {/* Stat Card */}
          <Card className="glass-panel border-white/10 overflow-hidden">
            <CardHeader className="bg-white/5 border-b border-white/5 py-4 px-6">
              <CardTitle className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-50 flex items-center gap-2">
                <FontAwesomeIcon
                  icon={faChartLine as IconProp}
                  className="w-3 h-3"
                />
                REPLAY METRICS
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-2 opacity-50">
                  Interval Load
                </p>
                <div className="flex items-end gap-2">
                  <span className="text-3xl font-black font-mono tracking-tighter">
                    {data.length}
                  </span>
                  <span className="text-[10px] font-black text-muted-foreground mb-1.5 uppercase opacity-30">
                    Ticks
                  </span>
                </div>
              </div>

              <div className="h-px bg-white/5 w-full" />

              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground mb-3 opacity-50">
                  Engine Status
                </p>
                {isConnected ? (
                  <Badge className="bg-emerald-500/10 text-emerald-500 border-none px-3 font-black tracking-widest text-[9px]">
                    STREAMING
                  </Badge>
                ) : isFinished ? (
                  <Badge className="bg-purple-500/10 text-purple-500 border-none px-3 font-black tracking-widest text-[9px]">
                    COMPLETED
                  </Badge>
                ) : (
                  <Badge className="bg-white/5 text-muted-foreground border-none px-3 font-black tracking-widest text-[9px]">
                    STANDBY
                  </Badge>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Hardware/Engine Note */}
          <Card className="glass-panel border-purple-500/20 bg-purple-500/5">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 text-purple-400 mb-3">
                <FontAwesomeIcon
                  icon={faMicrochip as IconProp}
                  className="w-4 h-4"
                />
                <h3 className="font-black text-[10px] uppercase tracking-widest">
                  Neural Sync Engine
                </h3>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed font-medium">
                Historical playback frequency target:{" "}
                <span className="text-foreground">2Hz</span> (0.5s/ stick). Data
                is streamed directly from Neural Core to your browser without
                frame-buffer delay. Animation smoothing disabled for 1:1
                real-time ticker replication fidelity.
              </p>
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-muted-foreground">
                <FontAwesomeIcon
                  icon={faForwardStep as IconProp}
                  className="w-3 h-3 opacity-20"
                />
                <span className="text-[9px] font-black uppercase opacity-20">
                  Latency: 0ms
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
