/**
 * Daftar simbol terpusat — harus konsisten dengan config_assets.py di backend.
 * Gunakan konstanta ini untuk semua dropdown pemilihan simbol di seluruh dashboard.
 */

export interface SymbolOption {
  value: string;
  label: string;
  category: "Saham IDX" | "Saham US" | "Crypto" | "Forex";
  flag?: string;
}

export const SYMBOL_OPTIONS: SymbolOption[] = [
  // Saham Indonesia
  { value: "BBCA.JK", label: "BBCA – Bank Central Asia", category: "Saham IDX", flag: "🇮🇩" },
  { value: "BBRI.JK", label: "BBRI – Bank Rakyat Indonesia", category: "Saham IDX", flag: "🇮🇩" },
  { value: "TLKM.JK", label: "TLKM – Telkom Indonesia", category: "Saham IDX", flag: "🇮🇩" },
  { value: "ASII.JK", label: "ASII – Astra International", category: "Saham IDX", flag: "🇮🇩" },
  { value: "GOTO.JK", label: "GOTO – GoTo Gojek Tokopedia", category: "Saham IDX", flag: "🇮🇩" },
  // Saham US
  { value: "AAPL", label: "AAPL – Apple Inc.", category: "Saham US", flag: "🇺🇸" },
  { value: "NVDA", label: "NVDA – NVIDIA Corporation", category: "Saham US", flag: "🇺🇸" },
  // Crypto
  { value: "BTC/USDT", label: "BTC/USDT – Bitcoin", category: "Crypto", flag: "₿" },
  { value: "ETH/USDT", label: "ETH/USDT – Ethereum", category: "Crypto", flag: "Ξ" },
  { value: "BNB/USDT", label: "BNB/USDT – Binance Coin", category: "Crypto", flag: "🔶" },
  { value: "SOL/USDT", label: "SOL/USDT – Solana", category: "Crypto", flag: "◎" },
  { value: "XRP/USDT", label: "XRP/USDT – Ripple", category: "Crypto", flag: "✕" },
  // Forex
  { value: "EURUSD=X", label: "EUR/USD – Euro / US Dollar", category: "Forex", flag: "🇪🇺" },
  { value: "GBPUSD=X", label: "GBP/USD – British Pound / USD", category: "Forex", flag: "🇬🇧" },
  { value: "JPY=X", label: "USD/JPY – US Dollar / Yen", category: "Forex", flag: "🇯🇵" },
  { value: "AUDUSD=X", label: "AUD/USD – Australian Dollar / USD", category: "Forex", flag: "🇦🇺" },
];

/** Simbol untuk backtest & simulation (hanya yang punya model) */
export const SYMBOL_OPTIONS_GROUPED = [
  {
    group: "🇮🇩 Saham IDX",
    options: SYMBOL_OPTIONS.filter((s) => s.category === "Saham IDX"),
  },
  {
    group: "🇺🇸 Saham US",
    options: SYMBOL_OPTIONS.filter((s) => s.category === "Saham US"),
  },
  {
    group: "₿ Crypto",
    options: SYMBOL_OPTIONS.filter((s) => s.category === "Crypto"),
  },
  {
    group: "💱 Forex",
    options: SYMBOL_OPTIONS.filter((s) => s.category === "Forex"),
  },
];
