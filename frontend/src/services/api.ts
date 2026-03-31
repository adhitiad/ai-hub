import axios from "axios";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/useAuthStore";
import type {
  LoginInput,
  LoginResponse,
  RegisterResponse,
  DashboardResponse,
  ChartDataResponse,
  MarketDepthResponse,
  CryptoSummary,
  BandarSummary,
  ForexSummary,
  SearchResult,
  ScreenerResponse,
  Alert,
  AlertCreateInput,
  TradeHistory,
  TradingStats,
  BacktestResult,
  ChatResponse,
  SubscriptionPlan,
  AdminUser,
  RevenueStats,
  UpgradeRequest,
  SystemStatus,
  AnalysisResult,
  PipelineStatus,
  SignalResponse,
  SignalStats,
} from "@/types";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 30000,
  withCredentials: true, // Izinkan pengiriman cookie
});

// Interceptor to add API key header from store (if present - legacy support)
api.interceptors.request.use(
  (config) => {
    // Kita tetap coba ambil dari store jika ada (misal di non-browser environment)
    // Tapi di browser modern, cookie akan menangani otentikasi.
    const token = useAuthStore.getState().apiKey;
    if (token) {
      config.headers["X-API-Key"] = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- 4. Global Error Interceptor (Auto Toast) ---
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const message = error.response?.data?.detail || error.response?.data?.message || "Terjadi kesalahan sistem";

    if (status === 401) {
      // Sesi kedaluwarsa atau tidak sah
      useAuthStore.getState().logout();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      toast.error("Sesi telah berakhir. Silakan login kembali.");
    } else if (status === 403) {
      toast.error("Akses ditolak: " + message);
    } else if (status === 429) {
      toast.error("Terlalu banyak permintaan (Rate Limit). Mohon tunggu sebentar.");
    } else if (status >= 500) {
      toast.error("Kesalahan Server: " + message);
    } else {
      // Hanya tampilkan toast jika bukan 404 (biasanya dihandel lokal)
      if (status !== 404) {
        toast.error(message);
      }
    }

    return Promise.reject(error);
  }
);

// ========== Auth ==========
export const authService = {
  login: (data: LoginInput) =>
    api.post<LoginResponse>("/auth/login", data),
  register: (data: { email: string; password: string }) =>
    api.post<RegisterResponse>("/auth/register", data),
  logout: () =>
    api.post("/auth/logout").finally(() => {
      useAuthStore.getState().logout();
    }),
};

// ========== Dashboard ==========
export const dashboardService = {
  getOverview: () =>
    api.get<DashboardResponse>("/dashboard/all"),
};

// ========== Market Data ==========
export const marketService = {
  getChart: (symbol: string, timeframe = "1h") =>
    api.get<ChartDataResponse>(`/market/chart/${encodeURIComponent(symbol)}`, {
      params: { timeframe },
    }),
  getDepth: (symbol: string) =>
    api.get<MarketDepthResponse>(`/market/depth/${symbol}`),
  getCryptoSummary: (symbol = "BTC/USDC") =>
    api.get<CryptoSummary>("/market/crypto/summary", { params: { symbol } }),
  getBandar: (symbol: string) =>
    api.get<BandarSummary>(`/market/bandar/${symbol}`),
  getForexSummary: (pair = "USDJPY") =>
    api.get<ForexSummary>("/market/forex/summary", { params: { pair } }),
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getSignal: (data: any) =>
    api.post("/market/get-signal", data),
};

// ========== Search ==========
export const searchService = {
  search: (q: string) =>
    api.get<SearchResult[]>("/search/", { params: { q } }),
};

// ========== Screener ==========
export const screenerService = {
  run: (params?: {
    min_score?: number;
    rsi_max?: number;
    rsi_min?: number;
    signal_only?: boolean;
    bandar_accum?: boolean;
  }) => api.get<ScreenerResponse>("/screener/run", { params }),
};

// ========== Alerts ==========
export const alertsService = {
  create: (data: AlertCreateInput) =>
    api.post("/alerts/create", data),
  list: () =>
    api.get<Alert[]>("/alerts/list"),
  delete: (alertId: string) =>
    api.delete(`/alerts/${alertId}`),
};

// ========== Journal ==========
export const journalService = {
  getHistory: (limit = 50) =>
    api.get<TradeHistory[]>("/journal/history", { params: { limit } }),
  getStats: () =>
    api.get<TradingStats>("/journal/stats"),
};

// ========== Backtest ==========
export const backtestService = {
  run: (symbol: string, period = "2y", balance = 100000000) =>
    api.get<BacktestResult>("/backtest/run", { params: { symbol, period, balance } }),
};

// ========== Portfolio ==========
export const portfolioService = {
  executeVirtual: (symbol: string, action: string, qty: number, price: number) =>
    api.post("/portfolio/execute-virtual", null, {
      params: { symbol, action, qty, price },
    }),
};

// ========== Chat ==========
export const chatService = {
  ask: (message: string, symbol?: string) =>
    api.post<ChatResponse>("/chat/ask", { message, symbol }),
};

// ========== User ==========
export const userService = {
  getWatchlist: () =>
    api.get<string[]>("/user/watchlist"),
  addWatchlist: (symbol: string) =>
    api.post("/user/watchlist/add", null, { params: { symbol } }),
  removeWatchlist: (symbol: string) =>
    api.delete("/user/watchlist/remove", { params: { symbol } }),
  updateBalance: (stock_idr: number, forex_usd: number) =>
    api.post("/user/settings/balance", { stock_idr, forex_usd }),
  checkSignal: (symbol: string) =>
    api.get(`/user/signal/check/${symbol}`),
  connectTelegram: (telegram_chat_id: string) =>
    api.post("/user/connect-telegram", { telegram_chat_id }),
  generateTelegramCode: () =>
    api.post("/user/generate-telegram-code"),
  regenerateApiKey: () =>
    api.post("/user/user/api-key/regenerate"),
};

// ========== Subscription ==========
export const subscriptionService = {
  getPlans: () =>
    api.get<Record<string, SubscriptionPlan>>("/subscription/plans"),
};

// ========== Admin ==========
export const adminService = {
  getUsers: (status = "all") =>
    api.get<AdminUser[]>("/admin/users", { params: { status } }),
  requestUpgrade: (target_role: string) =>
    api.post("/admin/user/request-upgrade", { target_role }),
  getUpgradeQueue: () =>
    api.get<UpgradeRequest[]>("/admin/admin/upgrade-queue"),
  executeUpgrade: (request_id: string, action: string, note = "") =>
    api.post("/admin/admin/execute-upgrade", { request_id, action, note }),
  approveUpgrade: (email: string, plan: string) =>
    api.post(`/admin/approve-upgrade/${email}`, null, { params: { plan } }),
  getRevenueStats: () =>
    api.get<RevenueStats>("/admin/revenue-stats"),
  searchUser: (q: string) =>
    api.get("/user/admin/search-user", { params: { q } }),
};

// ========== System ==========
export const systemService = {
  getStatus: () =>
    api.get<SystemStatus>("/"),
  healthCheck: () =>
    api.get("/health"),
  getMonitoringHealth: (symbol: string) =>
    api.get(`/monitoring/model-health/${symbol}`),
};

// ========== Analysis ==========
export const analysisService = {
  analyzePDF: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post<AnalysisResult>("/analysis/upload-report", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getLatest: (symbol: string) =>
    api.get<AnalysisResult>(`/analysis/latest/${symbol}`),
};

// ========== Pipeline ==========
export const pipelineService = {
  triggerOptimize: () =>
    api.post("/pipeline/optimize"),
  getStatus: () =>
    api.get<PipelineStatus>("/pipeline/status"),
};

// ========== Simulation ==========
export const simulationService = {
  startReplay: (symbol: string, start_time: string, end_time: string) =>
    api.post("/simulation/replay/start", { symbol, start_time, end_time }),
  pauseReplay: () =>
    api.post("/simulation/replay/pause"),
  resumeReplay: () =>
    api.post("/simulation/replay/resume"),
  stopReplay: () =>
    api.post("/simulation/replay/stop"),
  setSpeed: (speed: number) =>
    api.post("/simulation/replay/speed", { speed }),
  getStatus: () =>
    api.get("/simulation/replay/status"),
  testScenario: (symbol: string, shock_type: string) =>
    api.post("/simulation/scenario-test", { symbol, shock_type }),
};

// ========== Owner ==========
export const ownerService = {
  getFileTree: () =>
    api.get("/owner/files/tree"),
  readFile: (path: string) =>
    api.post("/owner/files/read", { path }),
  saveFile: (path: string, content: string) =>
    api.post("/owner/files/save", { path, content }),
  getLogsStream: () =>
    api.get("/owner/logs/stream"),
  triggerRetrain: () =>
    api.post("/owner/action/retrain"),
  restartBot: () =>
    api.post("/owner/action/restart-bot"),
  validateFix: (task: string) =>
    api.post("/owner/files/validate-fix", { task }),
  getDbView: (collectionName: string, limit = 50) =>
    api.get(`/owner/db/view/${collectionName}`, { params: { limit } }),
  getFinancialHealth: () =>
    api.get("/owner/financial-health"),
  getAuditLogs: (limit = 100) =>
    api.get("/owner/audit-logs", { params: { limit } }),
};

// ========== Assets ==========
export const assetsService = {
  /** Ambil semua simbol dari database. Fallback ke config statis jika DB kosong. */
  list: (category?: string) =>
    api.get<{ count: number; assets: AssetFromDB[]; source?: string }>(
      "/assets/list",
      { params: category ? { category } : {} }
    ),
};

// ========== Signals ==========
export const signalService = {
  list: (params: { status: "active" | "expired"; page: number; limit: number }) =>
    api.get<SignalResponse>("/signals/", { params }),
  getStats: () => api.get<SignalStats>("/signals/stats"),
};

/** Tipe satu aset dari DB (atau fallback config) */
export interface AssetFromDB {
  symbol: string;
  category: string;
  type: string;
  pip_scale?: number;
  lot_multiplier?: number;
  /** Label ramah manusia (opsional, bisa di-generate di frontend) */
  label?: string;
}
