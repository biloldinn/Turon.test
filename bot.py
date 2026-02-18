import requests
import time
import sys
import codecs

# Windows terminalida emoji/unicode muammosini hal qilish
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# --- Konfiguratsiyalar ---
TELEGRAM_BOT_TOKEN = "8247612744:AAHTKhj466aaqBbKHXefg6CD5v-abUMerv4"
TELEGRAM_CHAT_ID = "@turonntm95"
BASE_URL = "http://localhost:5000/api"
CHECK_INTERVAL = 180  # Har bir sikl orasida 3 minut kutish
DELAY_BETWEEN_USERS = 20  # Har bir odam orasida 20 sekund kutish

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def run_bot():
    print("Turon AI Telegram Bot (Qat'iy rejim) ishga tushdi...", flush=True)
    last_update_id = 0
    
    while True:
        try:
            # 1. /start buyrug'ini tahlil qilish (Polling)
            updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=1"
            try:
                upd_resp = requests.get(updates_url)
                updates = upd_resp.json().get("result", [])
                for update in updates:
                    last_update_id = update["update_id"]
                    if "message" in update and "text" in update["message"]:
                        text = update["message"]["text"]
                        chat_id = update["message"]["chat"]["id"]
                        if text == "/start":
                            send_telegram_message("<b>✅ Bot ishga tushdi!</b>\n\nMen har 3 minutda online o'quvchilarni guruhga chaqirib turaman.")
                            print(f"Botga /start bosildi (Chat ID: {chat_id})", flush=True)
            except:
                pass

            # 2. Oyna va davomiylikni tekshirish
            # Faqat har 3 minutda bir marta asosiy xabarni yuborish uchun vaqtni tekshiramiz
            # (Polling tezroq aylanishi kerak, lekin bildirishnomalar 3 minutda)
            
            # 1. Online o'quvchilarni olish
            try:
                online_resp = requests.get(f"{BASE_URL}/online-students", timeout=5)
                online_data = online_resp.json()
            except Exception as e:
                # Server o'chiq bo'lsa kutamiz
                print(f"Serverga ulanib bo'lmadi ({BASE_URL}). Tekshirilmoqda...", flush=True)
                time.sleep(5)
                continue

            online_users = online_data.get("students", [])
            online_ids = {str(u.get("id")): u for u in online_users}

            # 2. Barcha o'quvchilarni olish
            try:
                all_resp = requests.get(f"{BASE_URL}/bot/students", timeout=5)
                all_data = all_resp.json()
            except:
                continue

            all_students = all_data.get("students", [])
            if not all_students:
                time.sleep(5)
                continue

            to_mention = []
            for s in all_students:
                s_id = str(s.get("_id") or s.get("id"))
                name = f"{s.get('firstName')} {s.get('lastName')}"
                username = s.get("telegramUsername")
                phone = s.get("phone", "Noma'lum")
                
                # Chaqirish iyerarxiyasi:
                # 1. @username (agar bo'lsa) - bossa lichkasiga o'tadi
                # 2. tg://user?id=ID (bu faqat ayrim hollarda ishlaydi, shuning uchun ism + ID/nomer ko'rsatamiz)
                if username:
                    mention_name = f"@{username}"
                else:
                    # Username yo'q bo'lsa, ismi va telefon/ID orqali chaqiramiz
                    mention_name = f"<b>{name}</b> (ID: {s_id[-4:]} | 📱 {phone})"
                
                if s_id in online_ids:
                    to_mention.append(f"🌟 {mention_name} [ONLINE]")
                else:
                    to_mention.append(f"💤 {mention_name}")

            print(f"Sikl boshlandi: {len(to_mention)} ta total o'quvchi.", flush=True)

            # O'quvchilarni 10 tadan bo'lib chiqami
            for i in range(0, len(to_mention), 10):
                batch = to_mention[i:i+10]
                mention_text = "\n".join(batch)
                
                msg = f"<b>🔔 DIQQAT! DARSNI O'TKAZIB YUBORMANG!</b>\n\n{mention_text}\n\n"
                msg += "Iltimos, guruhga qo'shiling va darsda qatnashing! 🏃‍♂️💨"
                
                if send_telegram_message(msg):
                    print(f"Guruh yuborildi: {i}-{i+len(batch)}", flush=True)
                
                time.sleep(DELAY_BETWEEN_USERS)
                
                webinar_msg = "<b>🎁 Bepul vebinar dars tashkil qildik!</b>\n\nAzizlar, hozir chatga qo'shiling, juda muhim dars bo'lyapti! 🤗\n\n📍 <b>Guruh:</b> https://t.me/turonntm95"
                send_telegram_message(webinar_msg)
                
                if i + 10 < len(to_mention):
                    time.sleep(DELAY_BETWEEN_USERS)

            print(f"Sikl tugadi. {CHECK_INTERVAL} sekund kutish...", flush=True)
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print(f"Xatolik: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
