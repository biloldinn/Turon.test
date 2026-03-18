import time
from bot_instance import bot
from config import config
from logger import logger
import html

def handle_forwarding(message):
    cfg = config
    source = cfg.get('source_group')
    target = cfg.get('destination_group')

    if not cfg.get('is_forwarding_active') or not source or not target:
        return

    if str(message.chat.id) == str(source) or (message.chat.username and message.chat.username == str(source).replace('@', '')):
        try:
            # Handle user or channel/anonymous sender
            sender = message.from_user
            # Telegram Anonymous Bot ID
            is_anonymous_bot = sender and sender.id in [1087968824, 777000, 136817688]
            
            logger.info(f"Processing message {message.message_id}. Sender: {sender.id if sender else 'None'}, Chat: {message.chat.id}")

            # 1. Try to get real user or forward_from first
            if message.forward_from:
                sender = message.forward_from
            
            if sender and not is_anonymous_bot:
                full_name = html.escape(sender.first_name + (f" {sender.last_name}" if sender.last_name else ""))
                
                # Use mention_html if possible, or link to username/ID
                if sender.username:
                    profile_link = f"<a href='https://t.me/{sender.username}'>{full_name} (@{sender.username})</a>"
                else:
                    profile_link = f"<a href='tg://user?id={sender.id}'>{full_name}</a>"
            
            # 2. If anonymous admin or channel post
            elif message.sender_chat:
                chat = message.sender_chat
                name = html.escape(chat.title or "Mijoz")
                if chat.username:
                    profile_link = f"<a href='https://t.me/{chat.username}'>{name}</a>"
                else:
                    profile_link = f"<b>{name}</b> (Kanal/Guruh)"
            
            # 3. Fallback to forward_from_chat (if it's a channel forward)
            elif message.forward_from_chat:
                chat = message.forward_from_chat
                name = html.escape(chat.title or "Mijoz")
                if chat.username:
                    profile_link = f"<a href='https://t.me/{chat.username}'>{name} (Kanal)</a>"
                else:
                    profile_link = f"<b>{name}</b> (Kanal)"
            
            # 4. Fallback
            else:
                profile_link = "Noma'lum"

            # Format the profile link to be more prominent
            profile_html = f"👤 <b>Mijoz:</b> {profile_link}"
            logger.info(f"Generated profile HTML: {profile_html}")
            
            # Forward based on content type
            if message.text:
                new_text = f"📢 <b>Yangi xabar</b>\n\n{html.escape(message.text)}\n\n{profile_html}"
                bot.send_message(target, new_text, parse_mode="HTML")
            elif message.photo:
                caption = html.escape(message.caption or "")
                new_caption = f"📸 <b>Rasm xabari</b>\n{caption}\n\n{profile_html}"
                bot.send_photo(target, message.photo[-1].file_id, caption=new_caption, parse_mode="HTML")
            elif message.video:
                caption = html.escape(message.caption or "")
                new_caption = f"🎥 <b>Video xabari</b>\n{caption}\n\n{profile_html}"
                bot.send_video(target, message.video.file_id, caption=new_caption, parse_mode="HTML")
            else:
                # For other types, copy and send the profile info as a reply or separate message
                copied = bot.copy_message(target, message.chat.id, message.message_id)
                bot.send_message(target, f"☝️ Yuqoridagi xabar egasi:\n{profile_html}", 
                               parse_mode="HTML", reply_to_message_id=copied.message_id)

            logger.info(f"Message {message.message_id} forwarded with profile link to {target}")
            
            # Delete from source
            bot.delete_message(message.chat.id, message.message_id)
            logger.info(f"Message {message.message_id} deleted from source {message.chat.id}")
        except Exception as e:
            logger.error(f"Forwarding error: {e}")

# Separate handler for channel posts if needed
def handle_channel_forwarding(message):
    handle_forwarding(message)
