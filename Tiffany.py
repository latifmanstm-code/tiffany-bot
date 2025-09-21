import os
import logging
import pytesseract
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from deep_translator import GoogleTranslator
import qrcode

# Cek apakah onnxruntime tersedia
try:
    from rembg import remove
except ModuleNotFoundError:
    print("⚠️ Module 'onnxruntime' tidak ditemukan! Install dengan 'pip install rembg[onnx]'")
    remove = None  # agar bot tetap jalan untuk fitur lain

# === Konfigurasi ===
BOT_TOKEN = "7987228573:AAHRXIGXSV3pUHoxeniHnMQQgS2RxPKEXAk"
pytesseract.pytesseract.tesseract_cmd = "tesseract"

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Gambar Menjadi Tulisan", callback_data='ocr')],
        [InlineKeyboardButton("Hapus Latar Belakang", callback_data='remove_bg')],
        [InlineKeyboardButton("Buat QRIS", callback_data='buat_qr')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
    """Halo! Aku Tiffany Bot 🤖
Aku bisa bantu:
• Terjemahan: /translate <kode_bahasa>
• OCR: kirim foto saja
• Buat QRIS: /qris <teks>
• Hapus Latar Belakang: /hapus
• Lihat kode bahasa: /help""",
    reply_markup=reply_markup
)


# === /help ===
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    daftar = '''
🌍 Kode bahasa populer:

af = Afrikaans | ar = Arabic | de = German | en = English
es = Spanish | fr = French | hi = Hindi | id = Indonesian
it = Italian | ja = Japanese | jv = Javanese | ko = Korean
ms = Malay | pt = Portuguese | ru = Russian | th = Thai
tr = Turkish | vi = Vietnamese | zh-cn = Chinese (Simplified)
zh-tw = Chinese (Traditional)

📌 Contoh:
/translate id
/translate en
/qris https://example.com
/hapus
'''
    await update.message.reply_text(daftar)

# === /translate ===
async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Contoh: /translate en\n(untuk terjemah ke Inggris)")
        return
    target_lang = context.args[0].lower()
    context.user_data["translate_lang"] = target_lang
    await update.message.reply_text(f"✅ Mode terjemahan diaktifkan: {target_lang.upper()}.\nKirim teks apa saja untuk diterjemahkan.")

# === OCR otomatis saat kirim foto ===
async def ocr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    path = await file.download_to_drive()
    try:
        img = Image.open(path)
        text = pytesseract.image_to_string(img)
        await update.message.reply_text("📄 Hasil OCR:\n\n" + (text.strip() or "❌ Tidak ada teks terbaca."))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error OCR: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

# === Hapus Background Gambar ===
async def hapus_bg_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if remove is None:
        await update.message.reply_text(
            "⚠️ Fitur hapus background tidak tersedia. "
            "Install 'onnxruntime' dengan:\n`pip install rembg[onnx]`"
        )
        return

    if not update.message.photo:
        await update.message.reply_text("📸 Kirim foto untuk dihapus background-nya.")
        return

    file = await update.message.photo[-1].get_file()
    path = await file.download_to_drive()
    out_path = "no_bg.png"

    try:
        # Buka gambar
        input_image = Image.open(path)
        # Hapus background
        output_image = remove(input_image)
        # Simpan hasil
        output_image.save(out_path)

        # Kirim hasil ke Telegram
        with open(out_path, "rb") as out_file:
            await update.message.reply_photo(
                photo=out_file,
                caption="✅ Background berhasil dihapus!"
            )

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error hapus background: {e}")

    finally:
        # Hapus file sementara
        if os.path.exists(path):
            os.remove(path)
        if os.path.exists(out_path):
            os.remove(out_path)

# === Buat QRIS dari teks ===
async def buat_qr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kirim teks / alamat / email untuk dibuat QRIS.\nContoh: /qris https://example.com")
        return
    data = " ".join(context.args)
    out_path = "qris.png"
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save(out_path)
        await update.message.reply_photo(photo=open(out_path, "rb"), caption="✅ QRIS berhasil dibuat!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error membuat QRIS: {e}")
    finally:
        if os.path.exists(out_path): os.remove(out_path)

# === Teks biasa ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_lang = context.user_data.get("translate_lang")
    if target_lang:
        try:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(update.message.text)
            await update.message.reply_text(f"🌐 {translated}")
        except Exception as e:
            logging.error(f"Translate error: {e}")
            await update.message.reply_text("⚠️ Terjadi kesalahan saat menerjemahkan.")

# === Callback tombol ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "ocr":
        await query.message.reply_text("📸 Kirim foto untuk diubah menjadi teks.")
    elif query.data == "remove_bg":
        await query.message.reply_text("📸 Kirim foto untuk dihapus background-nya.")
    elif query.data == "buat_qr":
        await query.message.reply_text("✏️ Kirim teks / link / alamat untuk dibuat QRIS.")

# === Main ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("translate", translate_cmd))
    app.add_handler(CommandHandler("qris", buat_qr_cmd))
    app.add_handler(CommandHandler("hapus", hapus_bg_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, ocr))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
