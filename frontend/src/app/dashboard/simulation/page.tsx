"use client";

import { useState } from "react";
import { useSimulationSocket } from "@/hooks/useSimulationSocket";
import { Play, Square, FastForward, Activity, AlertCircle } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function SimulationPage() {
  const [symbol, setSymbol] = useState("BTC/USDT");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]); // default to today
  
  const [activeSim, setActiveSim] = useState<{ symbol: string; date: string } | null>(null);

  const {
    data,
    isConnected,
    isFinished,
    error,
    connect,
    disconnect,
  } = useSimulationSocket(activeSim?.symbol || "", activeSim?.date || "", false);

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
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-purple-400 bg-clip-text text-transparent">
            Time-Travel Simulation
          </h1>
          <p className="text-muted-foreground mt-1">
            Replay historical market conditions through Neural Engine WebSockets.
          </p>
        </div>
        
        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-3">
          <Input 
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="BTC/USDT"
            className="w-32 bg-white/5 border-white/10"
            disabled={isConnected}
          />
          <Input 
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-40 bg-white/5 border-white/10"
            disabled={isConnected}
          />
          {isConnected ? (
            <Button onClick={handleStop} className="bg-red-500/20 text-red-400 hover:bg-red-500/30">
              <Square className="w-4 h-4 mr-2 fill-current" /> Stop
            </Button>
          ) : (
            <Button onClick={handleStart} className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30">
              <Play className="w-4 h-4 mr-2 fill-current" /> Play Replay
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex flex-row items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Main Board */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="glass-panel p-6 rounded-xl border border-white/10 relative overflow-hidden min-h-[500px] flex flex-col">
            <div className="absolute top-0 right-0 p-32 bg-purple-500/5 blur-[100px] rounded-full pointer-events-none" />
            
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Activity className="w-5 h-5 text-purple-400" />
                Live Replay Chart {isConnected && <span className="ml-2 w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />}
                {isFinished && <span className="ml-2 text-xs font-normal text-muted-foreground">(Finished)</span>}
              </h2>
              
              <div className="text-right">
                <p className="text-sm text-muted-foreground tracking-wider uppercase font-mono">{activeSim?.symbol || symbol}</p>
                <p className={`text-2xl font-bold font-mono transition-colors ${
                  isUp ? "text-emerald-400" : "text-red-400"
                }`}>
                  {currentPrice.toFixed(2)}
                </p>
              </div>
            </div>

            <div className="flex-1 w-full mt-4">
              {data.length === 0 ? (
                <div className="h-full w-full flex flex-col items-center justify-center text-white/20">
                  <Play className="w-16 h-16 mb-4" />
                  <p>Start simulation to begin rendering</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#fff" strokeOpacity={0.05} />
                    <XAxis 
                      dataKey="time" 
                      tick={{ fill: "#666", fontSize: 10 }}
                      tickFormatter={(val) => {
                        const d = new Date(val);
                        return `${d.getHours()}:${d.getMinutes().toString().padStart(2, '0')}`;
                      }}
                    />
                    <YAxis 
                      domain={['auto', 'auto']} 
                      tick={{ fill: "#666", fontSize: 10 }}
                      tickFormatter={(val) => val.toFixed(0)}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: "#121212", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px" }}
                      labelStyle={{ color: "#999" }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="close" 
                      stroke="#10b981" 
                      strokeWidth={2} 
                      dot={false}
                      isAnimationActive={false} // Disable to avoid lag on fast updates
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-xl border border-white/10">
            <h3 className="font-medium text-sm text-muted-foreground uppercase tracking-wider mb-4">Replay Stats</h3>
            
            <div className="space-y-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Ticks Processed</p>
                <p className="text-xl font-bold font-mono">{data.length}</p>
              </div>
              
              <div>
                <p className="text-xs text-muted-foreground mb-1">Status</p>
                {isConnected ? (
                  <span className="inline-flex items-center text-xs font-semibold px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded">
                    STREAMING
                  </span>
                ) : isFinished ? (
                  <span className="inline-flex items-center text-xs font-semibold px-2 py-1 bg-white/10 text-white rounded">
                    ENDED
                  </span>
                ) : (
                  <span className="inline-flex items-center text-xs font-semibold px-2 py-1 bg-white/10 text-white/50 rounded">
                    IDLE
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="glass-panel p-6 rounded-xl border border-warning/10 bg-warning/5">
            <div className="flex items-center gap-2 text-warning mb-2">
              <FastForward className="w-4 h-4" />
              <h3 className="font-semibold text-sm">Engine Note</h3>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Simulation plays back historical candles fetched from the main database at roughly 0.5s intervals per stick to replicate live ticker condition. 
              The chart bypasses animation smoothing to render instantaneous updates securely.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
