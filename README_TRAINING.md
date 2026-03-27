# Implementasi Halaman Frontend untuk Semua Backend Routes

## Latar Belakang

Backend FastAPI memiliki **17 router** yang terdaftar di `main.py`. Saat ini frontend hanya meng-cover **2 dari 17** router (Auth + Dashboard). Perlu ditambahkan halaman dan service API untuk **15 router yang tersisa**, plus global endpoints.

## Pemetaan Router Backend → Frontend

### ✅ Sudah Diimplementasi

| Router             | Prefix       | Frontend                 |
| ------------------ | ------------ | ------------------------ |
| `auth_router`      | `/auth`      | ✅ `/login`, `/register` |
| `dashboard_router` | `/dashboard` | ✅ `/dashboard`          |

### 🔨 Perlu Diimplementasi (Dikelompokkan per Prioritas)

---

#### **Grup 1: Market & Trading Core** (Halaman utama user)

##### 1. Market Data (`/market`)

- `GET /market/chart/{symbol}` — OHLCV + Indikator (TradingView-like chart)
- `GET /market/depth/{symbol}` — Orderbook Bid/Offer
- `GET /market/crypto/summary` — Crypto whale data + Fear & Greed
- `GET /market/bandar/{symbol}` — Bandarmology (Akumulasi/Distribusi)
- `GET /market/forex/summary` — Forex strength meter
- `POST /market/get-signal` — AI signal request

**Frontend:** `/dashboard/market` — Halaman market data dengan tabs (Chart, Crypto, Forex, Bandar)

##### 2. Search (`/search`)

- `GET /search/?q=` — Cari aset berdasarkan simbol

**Frontend:** Komponen `SearchBar` di header/sidebar — autocomplete search dialog

##### 3. Screener (`/screener`)

- `GET /screener/run` — Filter aset berdasarkan indikator

**Frontend:** `/dashboard/screener` — Tabel filter-able dengan parameter RSI, signal, bandar

##### 4. Alerts (`/alerts`)

- `POST /alerts/create` — Buat alert baru
- `GET /alerts/list` — Daftar alert user
- `DELETE /alerts/{alert_id}` — Hapus alert

**Frontend:** `/dashboard/alerts` — CRUD tabel alerts + form create

---

#### **Grup 2: Analytics & Journal** (Performa trading)

##### 5. Journal (`/journal`)

- `GET /journal/history` — Riwayat trading
- `GET /journal/stats` — Statistik (Win Rate, Profit Factor, Drawdown, Equity Curve)

**Frontend:** `/dashboard/journal` — Tabel history + stats cards + equity curve Recharts

##### 6. Backtest (`/backtest`)

- `GET /backtest/run?symbol=&period=&balance=` — Jalankan backtest

**Frontend:** `/dashboard/backtest` — Form input (symbol, period, balance) + hasil backtest chart

##### 7. Portfolio (`/portfolio`)

- `POST /portfolio/execute-virtual` — Eksekusi order virtual

**Frontend:** `/dashboard/portfolio` — Virtual portfolio view + order form

---

#### **Grup 3: AI & Chat** (Fitur AI)

##### 8. Chat (`/chat`)

- `POST /chat/ask` — RAG-powered AI chat

**Frontend:** `/dashboard/chat` — Chat interface (bubble messages)

##### 9. Analysis (`/analysis`)

- `POST /analysis/upload-report` — Upload PDF laporan keuangan
- `GET /analysis/latest/{symbol}` — Ambil analisis terakhir

**Frontend:** `/dashboard/analysis` — Upload form + hasil analisis AI

##### 10. Pipeline (`/pipeline`)

- `POST /pipeline/optimize` — Trigger AI optimization
- `GET /pipeline/status` — Cek status optimization

**Frontend:** Tombol di admin area (bukan halaman terpisah)

---

#### **Grup 4: User Settings & Account**

##### 11. User (`/user`)

- `POST /user/connect-telegram` — Hubungkan Telegram
- `POST/DELETE/GET /user/watchlist` — Kelola watchlist
- `POST /user/settings/balance` — Set saldo trading
- `GET /user/signal/check/{symbol}` — Cek sinyal personal
- `POST /user/settings/telegram` — Simpan Telegram ID
- `POST /user/generate-telegram-code` — Buat kode binding Telegram
- `POST /user/user/api-key/regenerate` — Regenerate API key

**Frontend:** `/dashboard/settings` — Tab settings (Profile, Telegram, Balance, API Key, Watchlist)

##### 12. Subscription (`/subscription`)

- `GET /subscription/plans` — Daftar paket berlangganan

**Frontend:** `/dashboard/pricing` atau modal di settings

---

#### **Grup 5: Admin & Owner** (Akses terbatas)

##### 13. Admin (`/admin`)

- `GET /admin/users` — Lihat semua user
- `POST /admin/user/request-upgrade` — Request upgrade
- `GET /admin/admin/upgrade-queue` — Queue permintaan
- `POST /admin/admin/execute-upgrade` — Proses upgrade
- `POST /admin/approve-upgrade/{email}` — Approve user
- `GET /admin/revenue-stats` — Statistik revenue

**Frontend:** `/dashboard/admin` — Panel admin (tabel users, approve queue, revenue stats)

##### 14. Owner (`/owner`)

- `GET /owner/files/tree` — File explorer
- `POST /owner/files/read` — Baca file
- `POST /owner/files/save` — Simpan file
- `GET /owner/logs/stream` — Live log viewer
- `POST /owner/action/retrain` — Trigger retraining
- `POST /owner/action/restart-bot` — Restart bot logic
- `GET /owner/financial-health` — Financial metrics
- `GET /owner/audit-logs` — Audit logs
- dan lainnya...

**Frontend:** `/dashboard/owner` — Super admin panel (file editor, logs, training control)

##### 15. Simulation (`/simulation`)

- `WS /simulation/replay/{symbol}` — WebSocket replay market data

**Frontend:** `/dashboard/simulation` — Chart dengan replay control (play/pause/speed)

---

#### **Grup 6: Global Endpoints**

##### Root & Health

- `GET /` — System status
- `GET /health` — Health check
- `WS /ws/market/{symbol}` — Live market data

**Frontend:** Status badge di sidebar/footer

---

## Proposed Changes

### Fase 1 — Service Layer & Types (Foundation)

#### [MODIFY] [api.ts](file:///f:/code/ai-hub/frontend/src/services/api.ts)

Tambahkan semua fungsi API service untuk setiap endpoint.

#### [MODIFY] [types/index.ts](file:///f:/code/ai-hub/frontend/src/types/index.ts)

Tambahkan TypeScript interfaces untuk semua response types.

---

### Fase 2 — Updated Sidebar Navigation

#### [MODIFY] [sidebar.tsx](file:///f:/code/ai-hub/frontend/src/components/sidebar.tsx)

Tambahkan semua menu navigasi baru + role-based visibility (Admin/Owner menus).

---

### Fase 3 — Halaman-Halaman Baru

#### [NEW] `/dashboard/market/page.tsx` — Market Data (Chart, Crypto, Forex, Bandar)

#### [NEW] `/dashboard/screener/page.tsx` — Stock Screener

#### [NEW] `/dashboard/alerts/page.tsx` — Alerts Management

#### [NEW] `/dashboard/journal/page.tsx` — Trading Journal & Stats

#### [NEW] `/dashboard/backtest/page.tsx` — Backtest Playground

#### [NEW] `/dashboard/portfolio/page.tsx` — Virtual Portfolio

#### [NEW] `/dashboard/chat/page.tsx` — AI Chat Assistant

#### [NEW] `/dashboard/analysis/page.tsx` — Financial Report Analysis

#### [NEW] `/dashboard/settings/page.tsx` — User Settings

#### [NEW] `/dashboard/pricing/page.tsx` — Subscription Plans

#### [NEW] `/dashboard/admin/page.tsx` — Admin Panel

#### [NEW] `/dashboard/owner/page.tsx` — Owner Panel

#### [NEW] `/dashboard/simulation/page.tsx` — Time Travel Simulation

---

## User Review Required

> [!IMPORTANT]
> **Ini adalah pekerjaan sangat besar (13 halaman baru + infrastructure updates).** Apakah Anda ingin saya implementasi **semua sekaligus** atau **bertahap per grup**?

> [!WARNING]
> **Beberapa endpoint seperti `/simulation/replay` menggunakan WebSocket.** Implementasi WebSocket di Next.js memerlukan custom hook dan penanganan lifecycle khusus.

## Open Questions

1. **Prioritas:** Apakah Anda ingin saya mulai dari **Grup 1 (Market & Trading Core)** dulu, atau langsung semua?
2. **Chart Library:** Untuk `/market/chart/{symbol}` — ingin menggunakan **Recharts** (yang sudah ada) atau install **Lightweight Charts** (lebih cocok untuk candlestick trading)?
3. **Admin/Owner pages:** Apakah perlu dibuat lengkap, atau cukup placeholder dulu?

## Verification Plan

### Automated Tests

- `bun run build` harus berhasil tanpa error setelah setiap fase
- Semua route harus terdaftar di build output

### Manual Verification

- Jalankan `bun run dev` + backend FastAPI untuk test integrasi aktual
