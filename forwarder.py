import time
from bot_instance import bot
from config import config
from logger import logger
import html

def handle_forwarding(message):
    cfg = config
    source = cfg.get('source_group')
    target = cfg.get('destination_group')

    # Basic guards
    if not cfg.get('is_forwarding_active') or not source or not target:
        return

    # Check if message is from the source (either ID or username)
    is_from_source = False
    if str(message.chat.id) == str(source):
        is_from_source = True
    elif message.chat.username and message.chat.username == str(source).replace('@', ''):
        is_from_source = True

    if is_from_source:
        try:
            # 1. Get sender information and create profile link
            user = message.from_user
            if user:
                first_name = html.escape(user.first_name or "Mijoz")
                # Create a link that opens the user's private message
                if user.username:
                    profile_link = f"<a href='https://t.me/{user.username}'>{first_name}</a>"
                else:
                    profile_link = f"<a href='tg://user?id={user.id}'>{first_name}</a>"
            else:
                profile_link = "Yashirin profil"

            profile_html = f"👤 <b>Mijoz:</b> {profile_link}"

            # 2. Forward the content
            if message.text:
                clean_text = html.escape(message.text)
                forward_msg = f"📢 <b>Yangi xabar</b>\n\n📝 {clean_text}\n\n{profile_html}"
                bot.send_message(target, forward_msg, parse_mode="HTML")
            
            elif message.photo:
                cap = html.escape(message.caption or "")
                forward_cap = f"📸 <b>Rasm xabari</b>\n{cap}\n\n{profile_html}"
                bot.send_photo(target, message.photo[-1].file_id, caption=forward_cap, parse_mode="HTML")
            
            elif message.video:
                cap = html.escape(message.caption or "")
                forward_cap = f"🎥 <b>Video xabari</b>\n{cap}\n\n{profile_html}"
                bot.send_video(target, message.video.file_id, caption=forward_cap, parse_mode="HTML")
            
            else:
                # Other types: voice, document, etc.
                copied = bot.copy_message(target, message.chat.id, message.message_id)
                bot.send_message(target, f"☝️ Yuqoridagi xabar egasi:\n{profile_html}", 
                               parse_mode="HTML", reply_to_message_id=copied.message_id)

            logger.info(f"Message {message.message_id} forwarded and formatted.")

            # 3. DELETE the original message from source
            try:
                bot.delete_message(message.chat.id, message.message_id)
                logger.info(f"Source message {message.message_id} deleted successfully.")
            except Exception as d_err:
                logger.warning(f"Could not delete message: {d_err}. Ensure bot is ADMIN in source group.")

        except Exception as e:
            logger.error(f"Forwarding logic error: {e}")

def handle_channel_forwarding(message):
    # If source is a channel, same logic applies
    handle_forwarding(message)
