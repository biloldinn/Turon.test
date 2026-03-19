# Angren-Tosh Taxi & Post Telegram Bot

Professional Telegram bot for multi-group forwarding, order management, and advertisement automation.

## 🚀 Xususiyatlari (Features)
- **🚖 Buyurtma tizimi**: Taksi va Pochta xizmatlari uchun tugmalar va lokatsiya yuborish.
- **🔄 Avtomatik Forward**: Xabarlarni bir guruhdan ikkinchisiga mijoz profili bilan birga o'tkazish.
- **📢 Reklama tizimi**: Avtomatik taymer (interval) asosida rasmli yoki matnli reklamalar.
- **🛠 Admin Panel**: Bot sozlamalarini to'g'ridan-to'g'ri Telegram orqali boshqarish.
- **🐳 Docker Ready**: 24/7 uzluksiz ishlash uchun optimallashtirilgan.

## 🛠 Sozlash (Configuration)
1. `.env` fayliga `BOT_TOKEN`, `ADMIN_ID` va `WEBHOOK_URL` ni kiriting.
2. Botni ishga tushiring.
3. `/setgroups` komandasi orqali manba va qabul qiluvchi guruhlarni sozlang.

## 📜 Komandalar (Commands)
- `/start` - Botni boshlash
- `/admin` - Admin panelni ochish (faqat admin uchun)
- `/status` - Bot joriy holatini ko'rish
- `/setgroups` - Guruh ID larini sozlash

## 💻 Ishga tushirish (Running)
### Local (webhook):
```bash
python app.py
```
### Local (polling):
```bash
python local_polling.py
```
### Docker:
```bash
docker build -t taxi-bot .
docker run taxi-bot
```
