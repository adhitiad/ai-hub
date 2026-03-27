import { useState, useEffect, useRef, useCallback } from "react";
import { useAuthStore } from "@/stores/useAuthStore";

export interface SimulationTick {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function useSimulationSocket(symbol: string, date: string, autoConnect = false) {
  const [data, setData] = useState<SimulationTick[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isFinished, setIsFinished] = useState(false);
  const [error, setError] = useState<string>("");
  
  const wsRef = useRef<WebSocket | null>(null);
  const { apiKey } = useAuthStore();

  const connect = useCallback(() => {
    if (!symbol || !date) return;
    
    // reset state
    setData([]);
    setIsFinished(false);
    setError("");

    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const wsUrl = baseUrl.replace(/^http/, "ws") + `/simulation/replay/${encodeURIComponent(symbol)}?date=${date}`;
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const msg = event.data;
      if (msg === "No data found for this date." || msg === "Replay Finished") {
        setIsFinished(true);
        if (msg === "No data found for this date.") {
          setError(msg);
        }
        ws.close();
        return;
      }

      try {
        const tick = JSON.parse(msg) as SimulationTick;
        setData((prev) => [...prev, tick]);
      } catch (err) {
        console.error("Failed to parse sim tick", err);
      }
    };

    ws.onerror = (e) => {
      console.error("Simulation ws error", e);
      setError("WebSocket error occurred");
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    wsRef.current = ws;
  }, [symbol, date]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (autoConnect && symbol && date) {
      connect();
    }
    return () => disconnect();
  }, [autoConnect, symbol, date, connect, disconnect]);

  return {
    data,
    isConnected,
    isFinished,
    error,
    connect,
    disconnect,
  };
}
