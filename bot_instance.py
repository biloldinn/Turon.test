import telebot
from config import TOKEN
from logger import logger

if not TOKEN:
    logger.error("BOT_TOKEN is missing!")
    raise ValueError("BOT_TOKEN is missing!")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# Set bot commands
try:
    bot.set_my_commands([
        telebot.types.BotCommand("start", "Botni ishga tushirish"),
        telebot.types.BotCommand("admin", "Admin panel"),
        telebot.types.BotCommand("status", "Bot holatini ko'rish"),
        telebot.types.BotCommand("setgroups", "Guruhlarni sozlash")
    ])
except Exception as e:
    logger.error(f"Failed to set bot commands: {e}")

logger.info("Bot instance initialized.")
