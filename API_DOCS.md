# 📚 AI Trading Hub - API Documentation

**Base URL:** `http://localhost:8000`  
**Version:** v1.0  
**Format:** JSON

## 🔐 Authentication & Security

Semua endpoint (kecuali `/auth` dan `/payment/webhook`) dilindungi. Anda wajib menyertakan **API Key** di header setiap request.

| Header Name | Value                    | Description                       |
| :---------- | :----------------------- | :-------------------------------- |
| `X-API-KEY` | `your_generated_api_key` | Didapatkan setelah login/register |

---

## 1. Authentication

### Register User

Mendaftarkan pengguna baru dengan role default `free`.

- **URL:** `/auth/register`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "email": "trader@example.com",
    "password": "securepassword123"
  }
  ```

### Login

Masuk untuk mendapatkan API Key dan Role.

- **URL:** `/auth/login`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "email": "trader@example.com",
    "password": "securepassword123"
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "user": {
      "email": "trader@example.com",
      "role": "free",
      "api_key": "a1b2c3d4..." // <--- Simpan ini untuk Header X-API-KEY
    }
  }
  ```

---

## 2. Dashboard & Signals (Core)

### Get All Active Signals

Mengambil semua sinyal trading yang sedang aktif, lengkap dengan analisis AI, Bandarmology, dan Whale Detector.

- **URL:** `/dashboard/all`
- **Method:** `GET`
- **Headers:** `X-API-KEY: ...`
- **Response Example (Stock Indo):**
  ```json
  {
    "BBCA.JK": {
      "Symbol": "BBCA.JK",
      "Category": "STOCKS_INDO",
      "Action": "BUY",
      "Price": 9800,
      "Tp": 10200,
      "Sl": 9500,
      "LotSize": "50 Lot (5000 Lbr)",
      "Bandar_Info": {
        "Status": "ACCUMULATION",
        "Score": "85/100",
        "Message": "Big Player Hajar Kanan"
      },
      "AI_Analyst": {
        "Verdict": "FOLLOW",
        "Projected_Profit": "Rp 2.000.000",
        "Projected_Loss": "Rp 500.000",
        "Risk_Level": "3/10",
        "Note": "Volume spike detected aligns with technical breakout."
      }
    }
  }
  ```

---

## 3. Search & Navigation

### Global Search

Mencari aset berdasarkan simbol. Mendukung pencarian parsial (misal: "EUR").

- **URL:** `/search/?q={query}`
- **Method:** `GET`
- **Example:** `/search/?q=EUR`
- **Response:**
  ```json
  [
    {
      "symbol": "EURUSD=X",
      "category": "FOREX",
      "type": "forex",
      "status": "BUY",
      "has_signal": true
    }
  ]
  ```

---

## 4. User Features

### Add to Watchlist

Menambahkan simbol ke daftar pantauan pribadi.

- **URL:** `/user/watchlist/add`
- **Method:** `POST`
- **Query Param:** `?symbol=BBCA.JK`

### Get Watchlist

Melihat daftar pantauan.

- **URL:** `/user/watchlist`
- **Method:** `GET`

### Request Upgrade

Mengajukan perubahan role (Free -> Premium/Enterprise).

- **URL:** `/user/request-upgrade`
- **Method:** `POST`
- **Body:**

  ```json
  {
    "target_role": "premium"
  }
  ```

---

## 5. Admin Panel

### View Upgrade Queue

Melihat antrian user yang meminta upgrade.

- **URL:** `/admin/upgrade-queue`
- **Method:** `GET`
- **Requires Role:** `admin` or `owner`

### Execute Upgrade

Menyetujui atau menolak permintaan upgrade.

- **URL:** `/admin/execute-upgrade`
- **Method:** `POST`
- **Body:**
  ```json
  {
    "request_id": "663a1b2...", // MongoDB ID
    "action": "APPROVE", // or REJECT
    "note": "Payment verified via BCA"
  }
  ```

---

## 6. Owner Operations (God Mode)

### System Stats

Melihat beban server real-time.

- **URL:** `/owner/system/stats`
- **Method:** `GET`
- **Requires Role:** `owner`

### Stream Logs

Melihat 50 baris terakhir dari log server (termasuk error & aktivitas bot).

- **URL:** `/owner/logs/stream`
- **Method:** `GET`

### Retrain AI

Memaksa server untuk melatih ulang model AI di background.

- **URL:** `/owner/ai/retrain`
- **Method:** `POST`

### File Manager

- **List Files:** `GET /owner/files/tree`
- **Read File:** `POST /owner/files/read` (`{ "path": "main.py" }`)
- **Save File:** `POST /owner/files/save` (`{ "path": "main.py", "content": "..." }`)

---

## 7. Payments (Midtrans)

### Create Transaction

Membuat link pembayaran (Snap Token) untuk upgrade otomatis.

- **URL:** `/payment/create-transaction`
- **Method:** `POST`
- **Query Param:** `?plan=premium` (or `enterprise`)
- **Response:**
  ```json
  {
    "token": "snap_token_xyz...",
    "redirect_url": "[https://app.sandbox.midtrans.com/snap/](https://app.sandbox.midtrans.com/snap/)..."
  }
  ```

### Webhook

Endpoint yang dipanggil oleh Server Midtrans (Callback) saat pembayaran sukses. Tidak perlu dipanggil manual.

- **URL:** `/payment/webhook`
- **Method:** `POST`
