import os
import subprocess
import requests
from flask import Flask, request
import telebot
import openai

BOT_TOKEN = "9031697928:AAFqLQzUh9m7jYTqC8M4BCW1qoHbvOW38rE"
openai.api_key = "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"

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

def process_large_audio_ffmpeg(file_path):
    output_pattern = "chunk_%03d.mp3"
    command = [
        "ffmpeg", "-y", "-i", file_path, 
        "-f", "segment", "-segment_time", "600", 
        "-c", "copy", output_pattern
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    chunks = sorted([f for f in os.listdir('.') if f.startswith('chunk_') and f.endswith('.mp3')])
    full_text = ""
    
    for chunk_name in chunks:
        try:
            with open(chunk_name, "rb") as audio_file:
                transcript = openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ar"
                )
                full_text += transcript.text + " "
        except Exception as e:
            print(f"Error processing chunk: {e}")
        finally:
            if os.path.exists(chunk_name):
                os.remove(chunk_name)
                
    return full_text

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio_and_voice(message):
    processing_msg = bot.reply_to(message, "⏳ تم استلام ملفك في السيرفر السحابي! جاري التحميل والتقسيم...")
    
    file_id = message.audio.file_id if message.content_type == 'audio' else message.voice.file_id
    original_name = message.audio.file_name if message.content_type == 'audio' else f"voice_{message.from_user.id}.ogg"
    
    try:
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        
        download_url = f"https://telegram.org{BOT_TOKEN}/{file_path}"
        response = requests.get(download_url, stream=True)
        
        with open(original_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        final_text = process_large_audio_ffmpeg(original_name)
        
        if len(final_text) > 4000:
            for x in range(0, len(final_text), 4000):
                bot.reply_to(message, final_text[x:x+4000])
        else:
            bot.reply_to(message, f"📝 **النص المستخرج:**\n\n{final_text}")
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء سحب الملف. قيود تليجرام الصارمة قد تمنع تحميل ملفات ضخمة جداً مباشرة للسحاب بشكل تلقائي. يفضل تجربة ملف أصغر من 20MB للتأكد أولاً.")
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
    # 🛠️ التعديل السحري: يقوم السيرفر بربط وتفعيل نفسه تلقائياً بتليجرام بمجرد زيارة الرابط!
    webhook_url = f"https://onrender.com{BOT_TOKEN}"
    bot.remove_webhook()
    status = bot.set_webhook(url=webhook_url)
    if status:
        return "🎉 تم تفعيل وربط البوت بتليجرام بنجاح باهر! السيرفر يعمل الآن.", 200
    else:
        return "السيرفر يعمل ولكن فشل الربط التلقائي.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
