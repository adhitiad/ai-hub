# Training Files Documentation

Dokumentasi untuk file training yang disediakan:

## 1. train_single.py

File untuk melatih model single asset dengan konfigurasi yang mudah diatur.

### Usage:

```bash
# Melatih asset BBCA.JK dengan konfigurasi default
python train_single.py BBCA.JK

# Melatih asset dengan konfigurasi custom
python train_single.py BTCUSDT --timesteps 20000 --period 1y --interval 30m

# List semua asset yang tersedia di database
python train_single.py --list

# List asset berdasarkan kategori
python train_single.py --list --category crypto
```

### Parameters:

| Parameter       | Deskripsi                                                           | Default |
| --------------- | ------------------------------------------------------------------- | ------- |
| symbol          | Symbol asset yang akan dilatih (required)                           | -       |
| --timesteps, -t | Total timesteps untuk training                                      | 15000   |
| --period, -p    | Periode data yang akan diambil (contoh: 1y, 6mo, 30d)               | 2y      |
| --interval, -i  | Interval data (contoh: 5m, 15m, 1d)                                 | 1h      |
| --list, -l      | List semua asset yang tersedia                                      | False   |
| --category, -c  | Category asset untuk filtering (contoh: stocks_indo, crypto, forex) | None    |

## 2. train_batch.py

File untuk melatih beberapa asset sekaligus (batch training) dengan batasan concurrency.

### Usage:

```bash
# Melatih semua asset di kategori crypto
python train_batch.py --category crypto

# Melatih beberapa asset yang ditentukan
python train_batch.py --symbols "BBCA.JK,BRENTCrude,ETHUSDT" --timesteps 20000

# List semua kategori asset yang tersedia
python train_batch.py --list-categories
```

### Parameters:

| Parameter             | Deskripsi                                                                             | Default |
| --------------------- | ------------------------------------------------------------------------------------- | ------- |
| --category, -c        | Category asset yang akan dilatih (required jika tidak menggunakan --symbols)          | None    |
| --symbols, -s         | Daftar symbol asset dipisahkan oleh koma (required jika tidak menggunakan --category) | None    |
| --timesteps, -t       | Total timesteps untuk training                                                        | 15000   |
| --period, -p          | Periode data yang akan diambil (contoh: 1y, 6mo, 30d)                                 | 2y      |
| --interval, -i        | Interval data (contoh: 5m, 15m, 1d)                                                   | 1h      |
| --list-categories, -l | List semua kategori asset yang tersedia                                               | False   |

## 3. train_all.py (existing)

File untuk melatih semua asset di database secara paralel dengan batasan concurrency.

### Usage:

```bash
python train_all.py
```

## Output

Hasil training akan disimpan di folder `models/[category]/` dengan format nama file:

```
{symbol}_{date}_{timesteps}steps.zip
```

Contoh: `BBCA.JK_2024-02-05_15000steps.zip`

## Fitur Umum

1. **Auto-check model existence**: Skip training jika model dengan konfigurasi yang sama sudah ada
2. **Data validation**: Memeriksa apakah data yang diambil cukup untuk training
3. **Feature engineering**: Otomatis menambahkan indikator teknikal (RSI, MACD, dll.)
4. **Logging**: Logging yang jelas dengan emoji untuk memudahkan pembacaan
5. **Concurrency control**: Batasan jumlah training yang berjalan sekaligus untuk menghindari overload

## Catatan

- Pastikan database sudah di-seed sebelum menjalankan training
- Jika database kosong, jalankan `seed.py` terlebih dahulu
- Training membutuhkan waktu yang cukup sesuai dengan jumlah timesteps dan kompleksitas data
