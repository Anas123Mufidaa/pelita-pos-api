from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "laporan_uts.pdf"
NAVY = colors.HexColor("#15324B")
BLUE = colors.HexColor("#2A6F97")
LIGHT_BLUE = colors.HexColor("#EAF4FA")
GREEN = colors.HexColor("#2A9D68")
LIGHT_GRAY = colors.HexColor("#F4F6F8")
MUTED = colors.HexColor("#52616B")


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def make_table(data: list[list[object]], widths: list[float]) -> Table:
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.4),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CCD6DD")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def draw_page(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(colors.HexColor("#D6DEE3"))
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 9 * mm, "Pelita POS API - Laporan")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Halaman {document.page}")
    canvas.restoreState()


def build_report() -> None:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            textColor=NAVY,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontSize=13,
            leading=19,
            alignment=TA_CENTER,
            textColor=BLUE,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=21,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=9,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Subsection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=BLUE,
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyReport",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.4,
            leading=14,
            textColor=colors.HexColor("#263640"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Callout",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            textColor=NAVY,
            backColor=LIGHT_BLUE,
            borderColor=colors.HexColor("#B8D8EA"),
            borderWidth=0.6,
            borderPadding=9,
            spaceBefore=6,
            spaceAfter=9,
        )
    )

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title="Pelita POS API - Laporan",
        author="Pelita POS",
    )
    story: list[object] = []

    story.extend(
        [
            Spacer(1, 42 * mm),
            paragraph("PELITA POS API", styles["CoverTitle"]),
            paragraph(
                "Backend POS Asynchronous dengan FastAPI, aiosqlite, Concurrency Control, dan Load Testing",
                styles["CoverSubtitle"],
            ),
            Spacer(1, 18 * mm),
            Table(
                [
                    ["Deliverable", "Laporan Implementasi"],
                    ["Tanggal verifikasi", "14 November 2026"],
                    ["API", "Cashier dan Dashboard compatibility endpoints"],
                    ["Database", "SQLite asynchronous (aiosqlite)"],
                    ["Quality gate", "35 automated tests dan Ruff"],
                ],
                colWidths=[48 * mm, 92 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), NAVY),
                        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                        ("BACKGROUND", (1, 0), (1, -1), LIGHT_GRAY),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCD6DD")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                ),
                hAlign="CENTER",
            ),
            Spacer(1, 16 * mm),
            paragraph(
                "Tujuan: membuktikan API asynchronous, konsistensi response, pemrosesan transaksi background, pencegahan overselling, dan perbandingan performa satu dengan empat worker.",
                styles["Callout"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("1. Implementasi dan Arsitektur", styles["Section"]),
            paragraph(
                "Pelita POS API menggunakan FastAPI sebagai HTTP layer, Pydantic untuk validasi, dan aiosqlite untuk persistence asynchronous. Lifespan aplikasi menginisialisasi tabel saat startup. Request ID dibuat pada middleware dan diteruskan ke success maupun error envelope agar setiap response dapat ditelusuri.",
                styles["BodyReport"],
            ),
            paragraph("Alur request", styles["Subsection"]),
            make_table(
                [
                    ["Tahap", "Tanggung jawab"],
                    [
                        "HTTP router",
                        "Validasi parameter, dependency database path, status code, dan response model.",
                    ],
                    [
                        "Pydantic",
                        "Memastikan SKU, harga, stok, quantity, dan cashier name memenuhi batas domain.",
                    ],
                    [
                        "Database functions",
                        "Menjalankan query parameterized, transaction boundary, snapshot harga, dan pagination.",
                    ],
                    [
                        "Exception handler",
                        "Mengubah error menjadi envelope stabil tanpa membocorkan detail internal.",
                    ],
                ],
                [34 * mm, 128 * mm],
            ),
            paragraph("Endpoint utama", styles["Subsection"]),
            make_table(
                [
                    ["Method", "Path", "Sukses", "Fungsi"],
                    ["GET", "/health", "200", "Health check"],
                    ["GET", "/resource", "200", "Produk dan pagination"],
                    ["POST", "/resource", "201", "Buat produk, SKU unik"],
                    [
                        "GET/PUT/DELETE",
                        "/resource/{id}",
                        "200",
                        "Detail, update, hard delete",
                    ],
                    [
                        "POST",
                        "/transactions",
                        "202",
                        "Reservasi stok dan background processing",
                    ],
                    ["GET", "/transactions", "200", "Filter status dan pagination"],
                    ["GET", "/transactions/{id}", "200", "Detail transaksi"],
                ],
                [25 * mm, 50 * mm, 22 * mm, 65 * mm],
            ),
            paragraph("Data dan status transaksi", styles["Subsection"]),
            paragraph(
                "Produk menyimpan SKU unik, nama, kategori, harga integer, dan stok non-negatif. Transaksi menyimpan product ID, quantity, cashier, unit price, total price, timestamp, dan status. Harga disalin sebagai snapshot sehingga histori tidak berubah jika harga master diedit. Setelah response 202, background task mengubah pending menjadi processing, menunggu tiga detik, lalu completed; exception mengarahkan status ke failed.",
                styles["BodyReport"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("2. Concurrency dan Konsistensi Stok", styles["Section"]),
            paragraph(
                "Lost update terjadi ketika dua request membaca stok satu secara bersamaan. Keduanya menganggap barang tersedia, masing-masing membuat transaksi, lalu menulis hasil berdasarkan nilai lama. Constraint stok non-negatif tidak cukup: nilai akhir dapat tetap nol walaupun dua penjualan telah menerima unit yang sama.",
                styles["BodyReport"],
            ),
            paragraph("Eksperimen aktual", styles["Subsection"]),
            make_table(
                [
                    [
                        "Mode",
                        "Response 1",
                        "Response 2",
                        "Stok akhir",
                        "Penjualan sukses",
                    ],
                    ["Unsafe", "202", "202", "0", "2"],
                    ["Safe", "202", "409", "0", "1"],
                ],
                [32 * mm, 31 * mm, 31 * mm, 31 * mm, 37 * mm],
            ),
            paragraph(
                "Mode aman menggabungkan dua lapis proteksi. asyncio.Lock mengurutkan coroutine dalam satu process. Di database, BEGIN IMMEDIATE memperoleh write lock sebelum read-modify-write, lalu conditional update hanya mengurangi stok ketika stok masih mencukupi. Jika kondisi gagal, transaksi di-rollback dan API mengembalikan 409 INSUFFICIENT_STOCK.",
                styles["Callout"],
            ),
            paragraph("Mengapa dua lapis?", styles["Subsection"]),
            paragraph(
                "asyncio.Lock tidak dibagi antar-Uvicorn worker karena setiap worker adalah process terpisah. Karena itu lock Python hanya mengurangi contention lokal; database transaction adalah sumber kebenaran lintas worker. SQLite menserialisasi write secara luas. PostgreSQL production nantinya memerlukan row-level locking atau atomic conditional update yang diverifikasi dengan integration test database nyata.",
                styles["BodyReport"],
            ),
            paragraph("Bukti otomatis", styles["Subsection"]),
            make_table(
                [
                    ["Area", "Verifikasi"],
                    [
                        "Validation",
                        "Payload negatif, kosong, dan pagination invalid ditolak.",
                    ],
                    [
                        "Atomic stock",
                        "Dua koneksi independen terhadap stok terakhir: tepat satu berhasil.",
                    ],
                    [
                        "Background failure",
                        "Exception saat processing menghasilkan status failed.",
                    ],
                    [
                        "Response safety",
                        "Internal exception tidak membocorkan traceback atau detail database.",
                    ],
                    ["Regression", "35 test lulus pada verifikasi final."],
                ],
                [40 * mm, 122 * mm],
            ),
            PageBreak(),
        ]
    )

    benchmark_table = make_table(
        [
            ["Skenario", "Worker", "Req", "Fail", "Avg ms", "P95 ms", "Req/s"],
            ["GET /resource", "1", "100", "0", "42.72", "83", "266.21"],
            ["GET /resource", "4", "100", "0", "26.32", "92", "328.78"],
            ["POST /transactions", "1", "50", "0", "171.19", "260", "44.32"],
            ["POST /transactions", "4", "50", "0", "137.93", "410", "47.29"],
        ],
        [40 * mm, 18 * mm, 18 * mm, 18 * mm, 22 * mm, 22 * mm, 24 * mm],
    )
    story.extend(
        [
            paragraph("3. Benchmark dan Kesimpulan", styles["Section"]),
            paragraph(
                "Locust dijalankan terhadap Uvicorn lokal. Read memakai 20 user dan tepat 100 request; transaksi memakai 10 user dan tepat 50 request. Database di-reset sebelum setiap skenario. Seluruh hasil di bawah memiliki nol failure.",
                styles["BodyReport"],
            ),
            KeepTogether(
                [paragraph("Hasil aktual", styles["Subsection"]), benchmark_table]
            ),
            paragraph("Analisis", styles["Subsection"]),
            paragraph(
                "Empat worker menaikkan throughput read 23.5% dan menurunkan average latency 38.4%. Untuk transaksi, throughput meningkat 6.7% dan average latency turun 19.4%, tetapi P95 memburuk dari 260 ms menjadi 410 ms. Tail latency write yang lebih buruk menunjukkan contention SQLite walaupun beberapa process dapat menerima request secara paralel.",
                styles["BodyReport"],
            ),
            paragraph(
                "asyncio meningkatkan utilisasi saat coroutine menunggu I/O; ia bukan pengganti parallel CPU execution. Multi-worker menambah process dan event loop terpisah, sehingga dapat memakai beberapa core. Namun database tetap menjadi shared bottleneck. Benchmark singkat ini tidak boleh dianggap sebagai kapasitas production atau prediksi PostgreSQL.",
                styles["Callout"],
            ),
            paragraph("Kesimpulan dan keterbatasan", styles["Subsection"]),
            paragraph(
                "Implementasi ini membuktikan CRUD produk, transaksi asynchronous, response standard, validasi, race reproduction, pencegahan overselling, serta benchmark 1 dan 4 worker. SQLite dipertahankan sesuai rubrik. Keterbatasan saat ini adalah benchmark lokal bersampel kecil dan proses background in-memory yang dapat terhenti ketika server dimatikan. Scope sengaja dibatasi pada endpoint utama proyek.",
                styles["BodyReport"],
            ),
            paragraph(
                "Artefak pendukung: source FastAPI, automated tests, test_race.py, locustfile.py, CSV benchmark, README, dan panduan video. Video tetap memerlukan perekaman serta upload YouTube Unlisted oleh pemilik akun.",
                styles["BodyReport"],
            ),
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    build_report()
