import os
import logging
import pytesseract
from PIL import Image
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from deep_translator import GoogleTranslator

# === Konfigurasi ===
BOT_TOKEN = "7987228573:AAHRXIGXSV3pUHoxeniHnMQQgS2RxPKEXAk"

# === Logging ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Aku Tiffany Bot 🤖\n\n"
        "Aku bisa bantu:\n"
        "• Terjemahan: /translate <kode_bahasa>\n"
        "• OCR: kirim foto saja\n"
        "• Lihat kode bahasa: /help"
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
/translate ja
'''
    await update.message.reply_text(daftar)

# === /translate ===
async def translate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Contoh: /translate en\n(untuk terjemah ke Inggris)")
        return

    target_lang = context.args[0].lower()
    context.user_data["translate_lang"] = target_lang
    await update.message.reply_text(f"✅ Mode terjemahan diaktifkan: {target_lang.upper()}.\n"
                                    f"Kirim teks apa saja untuk diterjemahkan.")

# === OCR otomatis saat kirim foto ===
async def ocr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.photo[-1].get_file()
    path = await file.download_to_drive()

    try:
        if os.path.exists(path) and os.access(path, os.R_OK):
            img = Image.open(path)
            text = pytesseract.image_to_string(img)
            await update.message.reply_text("📄 Hasil OCR:\n\n" + (text.strip() or "❌ Tidak ada teks terbaca."))
        else:
            await update.message.reply_text("⚠️ File tidak bisa diakses: " + path)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error OCR: {e}")
    finally:
        if os.path.exists(path): os.remove(path)

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

# === Main ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("translate", translate_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, ocr))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()

if __name__ == "__main__":
    main()
