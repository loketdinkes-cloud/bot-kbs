# Panduan Setup Bot Telegram Pemicu Google Sheet

Berikut adalah langkah-langkah untuk menyiapkan dan menjalankan bot yang akan memantau baris baru di Google Sheet dan mengirim notifikasi ke Telegram.

## Prasyarat

1. [Python 3.7+](https://www.python.org/downloads/) terinstal
2. Akun Google untuk mengakses Google Cloud Console
3. Bot Telegram yang sudah dibuat (dengan token yang tersedia)
4. Google Sheet yang ingin Anda pantau (Anda sudah memberikan linknya)

## Langkah-langkah Setup

### 1. Buat Bot Telegram dan Dapatkan Token (Jika Belum Ada)

Jika Anda belum memiliki bot Telegram:
- Buka Telegram dan cari @BotFather
- Kirim `/newbot` dan ikuti instruksi untuk membuat bot baru
- Setelah berhasil, Anda akan menerima token bot (lihat seperti: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`)
- Salin token ini untuk digunakan nanti

### 2. Dapatkan Chat ID Tujuan Notifikasi

Untuk mengirim notifikasi ke chat tertentu:
- Buka obrolan dengan bot Anda di Telegram
- Kirim pesan apa saja ke bot
- Buka URL berikut di browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
  (ganti `<YOUR_BOT_TOKEN>` dengan token bot Anda)
- Cari objek `"chat"` dalam respons JSON dan catat nilai `"id"` (bisa berupa angka seperti `987654321`)
- Atau jika Anda ingin mengirim ke grup/channel, pastikan bot sudah menjadi anggota dan gunakan ID negatif untuk grup

### 3. Siapkan Google Sheet

Anda sudah memberikan link Google Sheet:
```
https://docs.google.com/spreadsheets/d/1jZGm_TyS5n7HVSAYUEutSDQ8NvS5xL0Da7iWFiwtX0M/edit?resourcekey=&gid=1747065779#gid=1747065779
```

Dari link tersebut, kami telah mengekstrak:
- **ID Spreadsheet**: `1jZGm_TyS5n7HVSAYUEutSDQ8NvS5xL0Da7iWFiwtX0M`

> ✅ Kami menggunakan **ID spreadsheet** (bukan nama) karena lebih stabil dan tidak berubah jika Anda mengganti judul sheet.

Pastikan sheet tersebut memiliki data (minimal header baris jika ingin diabaikan).

### 4. Buat Service Account dan Dapatkan Credentials

Ikuti langkah-langkah berikut untuk mengakses Google Sheet secara terprogram:

#### Langkah 1: Akses Google Cloud Console
- Buka [Google Cloud Console](https://console.cloud.google.com/)
- Pilih atau buat proyek baru

#### Langkah 2: Aktifkan Google Sheets API
- Di navigasi kiri, pilih "APIs & Services" > "Library"
- Cari "Google Sheets API"
- Klik dan pilih "Enable"

#### Langkah 3: Buat Service Account
- Di navigasi kiri, pilih "APIs & Services" > "Credentials"
- Klik "Create Credentials" > "Service account"
- Isi detail service account (nama bisa seperti: `google-sheets-bot`)
- Klik "Create and Continue"
- Anda dapat melewati pengaturan akses opsional dengan menekan "Done"

#### Langkah 4: Buat Kunci JSON
- Di daftar service account, cari akun yang baru saja Anda buat
- Klik pada nama service account
- Pilih tab "Keys"
- Klik "Add Key" > "Create new key"
- Pilih format "JSON"
- Klik "Create"
- File JSON akan otomatis diunduh ke komputer Anda
- **Pindahkan file yang diunduh ini ke direktori proyek ini dan rename menjadi `credentials.json`**

#### Langkah 5: Bagikan Google Sheet dengan Service Account
- Buka Google Sheet Anda (gunakan link di atas)
- Klik tombol "Share" di pojok kanan atas
- Tambahkan alamat email service account (terlihat seperti: `xxxx@yyyy.iam.gserviceaccount.com`)
  - Anda dapat menemukan email ini di file `credentials.json` pada field `"client_email"`
- Beri izin "Viewer" (cukup untuk membaca)
- Klik "Send"

### 5. Konfigurasi Variabel Lingkungan

File `.env` sudah saya perbarui dengan ID spreadsheet Anda. Silakan buka file `.env` dan isi nilai-nilai berikut:

```
TELEGRAM_BOT_TOKEN=your_actual_telegram_bot_token_here
GOOGLE_SHEET_ID=1jZGm_TyS5n7HVSAYUEutSDQ8NvS5xL0Da7iWFiwtX0M
TELEGRAM_CHAT_ID=your_telegram_chat_id_or_username_here
```

Contoh:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
GOOGLE_SHEET_ID=1jZGm_TyS5n7HVSAYUEutSDQ8NvS5xL0Da7iWFiwtX0M
TELEGRAM_CHAT_ID=987654321
```

### 6. Install Dependensi

Buka terminal atau command prompt di direktori proyek ini dan jalankan:

```bash
pip install -r requirements.txt
```

### 7. Jalankan Bot

Setelah semua langkah di atas selesai, jalankan bot dengan perintah:

```bash
python bot.py
```

Bot akan mulai berjalan dan memeriksa Google Sheet setiap 60 detik untuk baris baru.
Setiap kali ada baris baru yang terdeteksi, bot akan mengirim notifikasi ke Telegram.

### 8. Menghentikan Bot

Untuk menghentikan bot, tekan `Ctrl+C` di terminal tempat bot berjalan.

## Catatan Penting

- File `credentials.json` berisi informasi sensitif dan **tidak boleh** dibagikan atau di-commit ke repositori publik
- File `.env` juga berisi informasi sensitif dan harus disimpan dengan aman
- Bot akan membuat file `last_row.txt` secara otomatis untuk melacak baris terakhir yang diproses
- Pastikan komputer Anda tetap menyala dan terhubung ke internet saat bot berjalan jika Anda menjalankannya secara lokal
- Untuk menjalankan bot 24/7, pertimbangkan untuk mendeploy ke layanan seperti:
  - [Railway](https://railway.app/)
  - [Render](https://render.com/)
  - [AWS EC2](https://aws.amazon.com/ec2/)
  - VPS tradisional

## Pemecahan Masalah

### "Credentials file not found"
- Pastikan file `credentials.json` ada di direktori yang sama dengan `bot.py`
- Pastikan nama file tepat: `credentials.json` (case-sensitive)

### "Google Sheets API has not been used"
- Pastikan Anda telah mengaktifkan Google Sheets API di Google Cloud Console
- Tunggu beberapa saat setelah mengaktifkan API sebelum mencoba lagi

### "Invalid Credentials"
- Pastikan Anda menggunakan kunci JSON dari service account, bukan dari OAuth client ID
- Pastikan service account memiliki akses ke spreadsheet (langkah sharing sudah dilakukan)

### "Bot tidak mengirim notifikasi"
- Periksa log di terminal untuk pesan error
- Pastikan TELEGRAM_CHAT_ID benar (bisa berupa ID grup yang dimulai dengan tanda minus)
- Pastikan bot sudah mulai obrolan dengan pengguna (kirim `/start` ke bot terlebih dahulu jika menggunakan chat pribadi)

### "Bot berhenti setelah beberapa menit"
- Pastikan tidak ada error yang tidak ditangani yang menyebabkan crash
- Periksa koneksi internet Anda
- Pastikan tidak ada pembatasan kuota API (lebih jarang terjadi untuk penggunaan kecil)

## Catatan tentang ID Spreadsheet

Bot ini menggunakan **ID spreadsheet** (`1jZGm_TyS5n7HVSAYUEutSDQ8NvS5xL0Da7iWFiwtX0M`) yang Anda berikan melalui link. Ini berarti:
- Anda boleh ubah nama spreadsheet kapan saja tanpa merusak koneksi
- ID ini unik dan permanen untuk spreadsheet ini
- Jika Anda membuat salinan spreadsheet, ID akan berubah — pastikan Anda memperbarui `.env` jika menggunakan salinan

## Kontak dan Dukungan

Jika Anda mengalami kesulitan selama setup, silakan periksa file log yang dihasilkan oleh bot atau lihat output di terminal untuk petunjuk lebih detail.