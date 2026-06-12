import os
import time
import datetime
import json
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Bot
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# Path untuk penggunaan lokal (fallback)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

# Validate required environment variables
if not all([TELEGRAM_BOT_TOKEN, GOOGLE_SHEET_ID, TELEGRAM_CHAT_ID]):
    logger.error("Missing required environment variables. Please check your .env file.")
    exit(1)

# Initialize Telegram bot
try:
    # Initialize Bot object
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Telegram bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Telegram bot object: {e}")
    exit(1)

# Google Sheets setup
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

def initialize_google_sheets():
    """Initialize and return Google Sheets client."""
    try:
        # Prioritaskan environment variable untuk Cloud Hosting (Koyeb)
        if GOOGLE_CREDENTIALS_JSON:
            creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            logger.info("Google Sheets client initialized from Environment Variable")
        elif os.path.exists(CREDENTIALS_FILE):
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            logger.info("Google Sheets client initialized from local file")
        else:
            logger.error(f"Credentials file not found at: {CREDENTIALS_FILE}. "
                         "Please download it from Google Cloud Console.")
            return None

        client = gspread.authorize(creds)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets client: {e}")
        return None

def get_bot_status(client, key):
    """Mendapatkan nilai status dari sheet 'bot_status'."""
    try:
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        try:
            status_sheet = spreadsheet.worksheet('bot_status')
        except gspread.WorksheetNotFound:
            # Buat sheet status jika belum ada
            status_sheet = spreadsheet.add_worksheet(title='bot_status', rows="10", cols="2")
            status_sheet.update('A1:B4', [['key', 'value'], ['last_row', '0'], ['report_sent', ''], ['day_start', '']])
            logger.info("Created 'bot_status' worksheet")

        records = status_sheet.get_all_records()
        for row in records:
            if row['key'] == key:
                return row['value']
        return ""
    except Exception as e:
        logger.error(f"Error reading status {key}: {e}")
        return ""

def update_bot_status(client, key, value):
    """Memperbarui nilai status di sheet 'bot_status'."""
    try:
        status_sheet = client.open_by_key(GOOGLE_SHEET_ID).worksheet('bot_status')
        cell = status_sheet.find(key)
        status_sheet.update_cell(cell.row, cell.col + 1, str(value))
    except Exception as e:
        logger.error(f"Error updating status {key}: {e}")

def format_notification(row_data):
    """Format row data into a modern HTML message."""
    # Mapping berdasarkan urutan kolom baru:
    no_kk = row_data[3] if len(row_data) > 3 else "-"
    nik = row_data[4] if len(row_data) > 4 else "-"
    nama = row_data[5] if len(row_data) > 5 else "-"
    alamat = row_data[14] if len(row_data) > 14 else "-"
    kecamatan = row_data[15] if len(row_data) > 15 else "-"
    desa = row_data[16] if len(row_data) > 16 else "-"
    no_hp = row_data[19] if len(row_data) > 19 else "-"
    keterangan = row_data[22] if len(row_data) > 22 else "-"
    alasan = row_data[23] if len(row_data) > 23 else "-"
    link = str(row_data[21]).strip() if len(row_data) > 21 else ""

    msg = [
        "<b>✨ PENDAFTARAN BARU</b>",
        "━━━━━━━━━━━━━━━━━━",
        f"<b>No KK  :</b> <code>{no_kk}</code>",
        f"<b>NIK    :</b> <code>{nik}</code>",
        f"<b>Nama   :</b> {nama.upper()}",
        f"<b>Alamat :</b> {alamat}",
        f"<b>Desa   :</b> {desa}",
        f"<b>Kec    :</b> {kecamatan}",
        f"<b>No HP   :</b> <code>{no_hp}</code>",
        f"<b>Ket    :</b> {keterangan}",
        f"<b>Alasan :</b> {alasan}",
        "━━━━━━━━━━━━━━━━━━"
    ]

    # Tambahkan link WhatsApp otomatis jika nomor tersedia
    if no_hp != "-" and any(c.isdigit() for c in no_hp):
        clean_hp = "".join(filter(str.isdigit, no_hp))
        if clean_hp.startswith('0'): clean_hp = '62' + clean_hp[1:]
        msg.append(f"💬 <a href='https://wa.me/{clean_hp}'><b>Hubungi via WhatsApp</b></a>")

    if link.lower().startswith('http'):
        msg.append(f"👉 <a href='{link}'><b>Lihat Berkas</b></a>")
    else:
        msg.append("📁 <i>Berkas tidak tersedia</i>")

    return "\n".join(msg)

async def handle_daily_report(client, current_row_count):
    """Mengelola dan mengirim laporan ringkasan harian pada jam 15:00 WITA atau setelahnya."""
    wita_tz = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(wita_tz)
    today_str = now.strftime('%Y-%m-%d')
    
    # 1. Kelola data awal hari (untuk menghitung selisih data masuk hari ini)
    ds_date, ds_row = None, 0
    day_start_status = get_bot_status(client, 'day_start')
    
    if day_start_status:
        parts = day_start_status.split('|')
        if len(parts) == 2:
            ds_date, ds_row = parts[0], int(parts[1])
    
    if ds_date != today_str:
        # Jika hari baru terdeteksi, catat jumlah baris saat ini sebagai dasar perhitungan hari ini
        update_bot_status(client, 'day_start', f"{today_str}|{current_row_count}")
        ds_row = current_row_count
        logger.info(f"Titik awal data hari ini diperbarui ({today_str}): {ds_row}")

    # 2. Cek apakah sudah jam 15:00 WITA (atau setelahnya) dan belum kirim laporan hari ini
    if now.hour >= 15:
        last_report_sent = get_bot_status(client, 'report_sent')
        already_sent = (last_report_sent == today_str)

        if not already_sent:
            daily_total = max(0, current_row_count - ds_row)
            report_msg = [
                "📊 <b>LAPORAN HARIAN</b>",
                f"📅 Tanggal: {now.strftime('%d-%m-%Y')}",
                "🕒 Waktu: 15:00 WITA",
                "━━━━━━━━━━━━━━━━━━",
                f"✅ Total data masuk hari ini: <b>{daily_total}</b>",
                "━━━━━━━━━━━━━━━━━━"
            ]
            try:
                await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="\n".join(report_msg), parse_mode='HTML')
                update_bot_status(client, 'report_sent', today_str)
                logger.info(f"Laporan harian terkirim untuk {today_str}: {daily_total} data")
            except Exception as e:
                logger.error(f"Gagal mengirim laporan harian: {e}")

async def check_for_new_rows(client):
    """Check for new rows in Google Sheet and send notifications."""
    try:
        # Open the spreadsheet by ID
        sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
        
        # Get all values
        all_values = sheet.get_all_values()
        if not all_values:
            logger.warning("Sheet is empty")
            return
        
        current_row_count = len(all_values)
        status_val = get_bot_status(client, 'last_row')
        last_processed = int(status_val) if status_val and str(status_val).isdigit() else 0

        logger.info(f"Current rows: {current_row_count}, Last processed: {last_processed}")
        
        # Check if there are new rows
        if current_row_count > last_processed:
            # Kasus Pertama: Jika file log belum ada (Cold Start)
            if last_processed == 0:
                # Tandai semua baris lama sebagai 'sudah diproses' agar tidak spam notifikasi
                logger.info(f"First run: Initializing with {current_row_count} existing rows.")
                update_bot_status(client, 'last_row', current_row_count)
                return

            # Ambil data baru saja (start dari index last_processed)
            new_rows = all_values[last_processed:]

            if new_rows:
                logger.info(f"Found {len(new_rows)} new row(s) to process")
                for i, row in enumerate(new_rows):
                    actual_row_number = last_processed + i + 1
                    message = format_notification(row)
                    
                    try:
                        await bot.send_message(
                            chat_id=TELEGRAM_CHAT_ID, 
                            text=message,
                            parse_mode='HTML'
                        )
                        logger.info(f"Notification sent for row {actual_row_number}")
                    except Exception as e:
                        logger.error(f"Failed to send Telegram notification: {e}")

                update_bot_status(client, 'last_row', current_row_count)
        elif current_row_count < last_processed:
            # Kasus: Ada data yang dihapus
            logger.info(f"Deteksi: Data dihapus atau dikurangi. Menyesuaikan log dari {last_processed} ke {current_row_count}")
            update_bot_status(client, 'last_row', current_row_count)
        else:
            logger.debug("No new rows found")
            
        # Periksa dan kirim laporan harian jika sudah waktunya
        await handle_daily_report(client, current_row_count)
            
    except Exception as e:
        logger.error(f"Error checking for new rows: {e}", exc_info=True)

async def main():
    """Main function to run the bot."""
    logger.info("Starting Google Sheets to Telegram notification bot...")
    
    # Initialize Google Sheets client
    client = initialize_google_sheets()
    if not client:
        logger.error("Failed to initialize Google Sheets client. Exiting.")
        return
    
    logger.info("Bot is now running and checking for new rows every minute...")
    
    # Main loop
    while True:
        try:
            await check_for_new_rows(client)
            await asyncio.sleep(60)  # Wait for 60 seconds before next check
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            logger.info("Waiting 60 seconds before retrying...")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())