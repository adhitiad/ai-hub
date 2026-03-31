import { z } from "zod";

// ========== Auth Schemas ==========
export const LoginSchema = z.object({
  email: z.string().email("Email tidak valid"),
  password: z.string().min(6, "Password minimal 6 karakter"),
});

export type LoginInput = z.infer<typeof LoginSchema>;

export const RegisterSchema = z.object({
  email: z.string().email("Email tidak valid"),
  password: z.string().min(6, "Password minimal 6 karakter"),
  confirmPassword: z.string().min(6, "Konfirmasi password minimal 6 karakter"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Password tidak cocok",
  path: ["confirmPassword"],
});

export type RegisterInput = z.infer<typeof RegisterSchema>;

// ========== Auth Response ==========
export const LoginResponseSchema = z.object({
  status: z.string(),
  user: z.object({
    email: z.string(),
    role: z.string(),
    api_key: z.string(),
  }),
});

export type LoginResponse = z.infer<typeof LoginResponseSchema>;

export const RegisterResponseSchema = z.object({
  status: z.string(),
  message: z.string(),
  api_key: z.string(),
  code: z.number(),
});

export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;

// ========== Dashboard ==========
export interface SignalItem {
  symbol: string;
  Action?: string;
  Confidence?: number;
  Price?: number;
  TP?: number | string;
  SL?: number | string;
  [key: string]: unknown;
}

export interface SignalCounts {
  BUY: number;
  SELL: number;
  HOLD: number;
  OTHER: number;
}

export interface DashboardResponse {
  status: string;
  server_time: string;
  signals: {
    total: number;
    counts: SignalCounts;
    items: SignalItem[];
  };
  open_trades: OpenTrade[];
}

export interface OpenTrade {
  id?: string;
  symbol: string;
  action: string;
  entry_price?: number;
  current_price?: number;
  pnl?: number;
  status: string;
  created_at?: string;
  [key: string]: unknown;
}

// ========== Market Data ==========
export interface ChartCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma20?: number;
  sma50?: number;
  rsi?: number;
  bandar_accum?: number;
}

export interface ChartDataResponse {
  symbol: string;
  data: ChartCandle[];
}

export interface OrderBookEntry {
  price: number;
  vol: number;
}

export interface MarketDepthResponse {
  symbol: string;
  status: string;
  bids: OrderBookEntry[];
  offers: OrderBookEntry[];
}

export interface CryptoSummary {
  symbol: string;
  fear_greed: number;
  net_flow: string;
  action: string;
  score: number;
  exchange: string;
  timestamp: string;
}

export interface BandarSummary {
  symbol: string;
  status: string;
  score: number;
  message: string;
  vol_ratio: number;
}

export interface ForexSummary {
  pair: string;
  base_currency: string;
  quote_currency: string;
  strength: Record<string, number>;
  signal: string;
  session: string;
  timestamp: string;
}

// ========== Search ==========
export interface SearchResult {
  symbol: string;
  category: string;
  type: string;
  status: string;
  has_signal: boolean;
}

// ========== Screener ==========
export interface ScreenerResponse {
  count: number;
  matches: SignalItem[];
}

// ========== Alerts ==========
export interface Alert {
  id?: string;
  _id?: string;
  symbol: string;
  type: string;
  condition: string;
  target_price: number;
  note: string;
  status: string;
  created_at?: string;
}

export interface AlertCreateInput {
  symbol: string;
  type: string;
  condition: string;
  target_price?: number;
  note?: string;
}

// ========== Journal ==========
export interface TradeHistory {
  id?: string;
  _id?: string;
  symbol: string;
  action: string;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  entry_date?: string;
  exit_date?: string;
  pnl?: number;
  pnl_percent?: number;
  status: string;
  [key: string]: unknown;
}

export interface TradingStats {
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  total_pnl_percent: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  max_drawdown: number;
  best_trade: number;
  worst_trade: number;
  equity_curve: number[];
  avg_risk_reward?: string;
  net_pnl?: number;
}

// ========== Backtest ==========
export interface BacktestResult {
  symbol?: string;
  period?: string;
  total_trades?: number;
  win_rate?: number;
  net_pnl?: number;
  max_drawdown?: number;
  sharpe_ratio?: number;
  trades?: TradeHistory[];
  equity_curve?: number[];
  [key: string]: unknown;
}

// ========== Portfolio ==========
export interface PortfolioItem {
  symbol: string;
  qty: number;
  avg_price: number;
  date?: string;
}

// ========== Chat ==========
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string;
  timestamp?: Date;
}

export interface ChatResponse {
  answer: string;
  sources?: string;
}

// ========== Subscription ==========
export interface SubscriptionPlan {
  name: string;
  price: number;
  features: string[];
  daily_requests_limit: number;
  [key: string]: unknown;
}

// ========== Admin ==========
export interface AdminUser {
  _id: string;
  email: string;
  role: string;
  subscription_status?: string;
  daily_requests_limit?: number;
  requests_today?: number;
  created_at?: string;
  [key: string]: unknown;
}

export interface RevenueStats {
  total_users: number;
  breakdown: Record<string, number>;
  monthly_revenue_usd: number;
  last_updated: string;
}

export interface UpgradeRequest {
  _id?: string;
  id?: string;
  user_email: string;
  requested_role: string;
  status: string;
  created_at: string;
  admin_note: string;
}

// ========== System ==========
export interface SystemStatus {
  status: string;
  system: string;
  version: string;
  environment: string;
  server_time: string;
  cpu_usage: string;
  ram_usage: string;
  cfg?: {
    signal_agent?: { enabled: boolean };
    dependencies_configured?: { redis: boolean; mongo: boolean };
  };
}

// ========== Analysis ==========
export interface AnalysisResult {
  symbol: string;
  summary: string;
  sentiment: string;
  key_metrics?: Record<string, string | number>;
  pdf_url?: string;
  created_at?: string;
}

// ========== Pipeline ==========
export interface PipelineStatus {
  status: "idle" | "running" | "completed" | "failed";
  progress: number;
  message?: string;
  last_run?: string;
  eta?: string;
}

// ========== Simulation ==========
export interface SimulationTick {
  symbol: string;
  timestamp: string;
  price: number;
  volume?: number;
  action?: "BUY" | "SELL" | "HOLD";
}

// ========== Signals ==========
export interface TradingSignal {
  id: string;
  symbol: string;
  action: string;
  price: number;
  tp: number;
  sl: number;
  lot_size: string;
  status: string;
  rank?: "ELITE" | "PREMIUM" | "SPECULATIVE";
  asset_type?: string;
  created_at: string;
  Prob?: string;
  AI_Analysis?: string;
  [key: string]: unknown;
}

export interface SignalResponse {
  status: string;
  total: number;
  page: number;
  limit: number;
  data: TradingSignal[];
}

export interface SignalStats {
  win_rate: number;
  total_signals: number;
  wins: number;
  losses: number;
}
