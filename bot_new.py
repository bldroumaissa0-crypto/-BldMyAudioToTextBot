import os
import time
import requests
from flask import Flask, request
import telebot
import google.generativeai as genai

# توكن بوت تليجرام الخاص بك جاهز ومدمج
BOT_TOKEN = "9031697928:AAFqLQzUh9m7jYTqC8M4BCW1qoHbvOW38rE"

# ⚠️ ضع هنا مفتاح جوجل جيميناي (Gemini) الذي نسخته بين علامتي التنصيص
GOOGLE_API_KEY = "AQ.Ab8RN6LnpAp9m07DpxykdG3lNdui0A3X5ekkLDc6Ontou3v8Gw"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

genai.configure(api_key=GOOGLE_API_KEY)

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio_and_voice(message):
    processing_msg = bot.reply_to(message, "⏳ ذكاء Google Gemini استلم ملفك الصوتي الضخم! جاري معالجته وتحويله إلى نص بدقة عالية، انتظر ثوانٍ...")
    
    file_id = message.audio.file_id if message.content_type == 'audio' else message.voice.file_id
    original_name = "temp_audio.mp3" if message.content_type == 'audio' else "temp_audio.ogg"
    
    try:
        file_info = bot.get_file(file_id)
        download_url = f"https://telegram.org{BOT_TOKEN}/{file_info.file_path}"
        
        response = requests.get(download_url, stream=True)
        with open(original_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        print("📥 جاري رفع الصوت لذكاء جوجل...")
        audio_file = genai.upload_file(path=original_name)
        
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = genai.get_file(audio_file.name)
            
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        result = model.generate_content([audio_file, "قم بتفريغ هذا الملف الصوتي وكتابة النص كاملاً باللغة العربية بدقة عالية وبدون تلخيص"])
        
        final_text = result.text
        
        if len(final_text) > 4000:
            for x in range(0, len(final_text), 4000):
                bot.reply_to(message, final_text[x:x+4000])
        else:
            bot.reply_to(message, f"📝 **النص المستخرج بالكامل عبر Google Gemini:**\n\n{final_text}")
            
        genai.delete_file(audio_file.name)
        
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء المعالجة.\nتفاصيل: {e}")
    finally:
        if os.path.exists(original_name):
            os.remove(original_name)
        bot.delete_message(message.chat.id, processing_msg.message_id)

@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    webhook_url = f"https://onrender.com{BOT_TOKEN}"
    bot.remove_webhook()
    status = bot.set_webhook(url=webhook_url)
    if status:
        return "🎉 تم تفعيل وربط بوت Google Gemini بنجاح باهر! السيرفر يعمل الآن مجاناً.", 200
    else:
        return "فشل الربط التلقائي.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
