# Pelita POS API Benchmark Results

Benchmark dijalankan pada 14 November 2026 menggunakan Locust 2.47.0 terhadap
Uvicorn lokal. Skenario read memakai 20 concurrent users dan tepat 100 request.
Skenario transaksi memakai 10 concurrent users dan tepat 50 request. Data di-reset
sebelum setiap skenario. Semua angka berikut berasal dari baris `Aggregated` pada
CSV yang disimpan di direktori ini.

| Skenario | Worker | Request | Failure | Avg (ms) | P95 (ms) | Request/s | Total Waktu (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `GET /resource` | 1 | 100 | 0 | 55.89 | 120 | 216.78 | 0.46 |
| `GET /resource` | 4 | 100 | 0 | 39.27 | 130 | 277.44 | 0.36 |
| `POST /transactions` | 1 | 50 | 0 | 144.31 | 190 | 50.09 | 1.00 |
| `POST /transactions` | 4 | 50 | 0 | 137.59 | 530 | 53.52 | 0.93 |

Empat worker meningkatkan throughput read sekitar 28.0% dan menurunkan average
latency sekitar 29.7%. Pada transaksi, throughput meningkat sekitar 6.8% dan
average latency turun sekitar 4.7%, tetapi P95 memburuk dari 190 ms menjadi 530
ms. Hasil write ini konsisten dengan contention SQLite: beberapa process dapat
melayani request secara paralel, tetapi write tetap diserialisasi oleh database.
Karena sampel singkat, angka ini merupakan bukti eksperimen lokal, bukan kapasitas
production.

## Reproduction

1. Jalankan `python benchmark_setup.py` sebelum setiap skenario.
2. Jalankan API dengan `uvicorn main:app --port 8000` untuk satu worker.
3. Ulangi dengan `uvicorn main:app --workers 4 --port 8000`.
4. Gunakan perintah Locust pada README dan sesuaikan prefix `--csv`.

`REQUEST_LIMIT` pada `locustfile.py` membatasi jumlah request yang diklaim oleh
virtual users. `-t 5s` memberi Locust waktu menulis statistik final setelah semua
virtual users berhenti.
