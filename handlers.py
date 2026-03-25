from bot_instance import bot
from config import config, save_config, ADMIN_IDS
from logger import logger
from telebot import types
import html
import ads
import forwarder
from datetime import datetime, timedelta

user_states = {}

def is_admin(message_or_call):
    """Works for both Message and CallbackQuery objects."""
    if hasattr(message_or_call, 'from_user') and message_or_call.from_user:
        uid = message_or_call.from_user.id
    elif hasattr(message_or_call, 'id'):
        uid = message_or_call.id
    else:
        return False
    return int(uid) in ADMIN_IDS

def register_handlers():

    @bot.message_handler(commands=['start'])
    def start(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🚖 Taksi chaqirish"), types.KeyboardButton("📦 Pochta jo'natish"))

        welcome_text = (
            f"🌟 <b>Assalomu alaykum, {html.escape(message.from_user.first_name)}!</b>\n\n"
            "Bizning xizmatimizdan foydalanganingiz uchun rahmat. "
            "Sizga qanday yordam bera olamiz? Quyidagi tugmalardan birini tanlang:"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="HTML")

    @bot.message_handler(commands=['status'])
    def status(message):
        s = config.get('source_group') or '<i>Sozlanmagan</i>'
        d = config.get('destination_group') or '<i>Sozlanmagan</i>'
        ad_g = config.get('ad_target_group') or s

        status_text = (
            f"📊 <b>Bot Holati</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📤 <b>Manba:</b> <code>{s}</code>\n"
            f"📥 <b>Qabul qiluvchi:</b> <code>{d}</code>\n"
            f"📢 <b>Reklama guruhi:</b> <code>{ad_g}</code>\n"
            f"🔄 <b>Forwarding:</b> {'🟢 ON' if config.get('is_forwarding_active') else '🔴 OFF'}\n"
            f"📢 <b>Reklama:</b> {'🟢 ON' if config.get('is_ad_active') else '🔴 OFF'}\n"
            f"⏳ <b>Interval:</b> <code>{config.get('ad_interval_minutes')}</code> minut\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(message.chat.id, status_text, parse_mode="HTML")

    @bot.message_handler(commands=['setgroups'])
    def set_groups_start(message):
        if not is_admin(message):
            return
        bot.send_message(message.chat.id,
            "📤 <b>Manba guruh/kanal ID sini yuboring:</b>\n"
            "(Masalan: -100123456789 yoki @username)", parse_mode="HTML")
        user_states[message.chat.id] = 'setting_source'

    @bot.message_handler(commands=['admin'], func=lambda m: is_admin(m))
    def admin_panel(message):
        status_ad = "🟢 YOQILGAN" if config.get('is_ad_active') else "🔴 O'CHIRILGAN"
        status_fwd = "🟢 YOQILGAN" if config.get('is_forwarding_active') else "🔴 O'CHIRILGAN"

        ad_text_preview = (config.get('ad_text', '')[:40] + "...") if config.get('ad_text') else "Mavjud emas"

        panel_text = (
            f"🛠 <b>Admin Panel</b>\n\n"
            f"📢 <b>Reklama:</b> {status_ad}\n"
            f"⏳ <b>Interval:</b> {config.get('ad_interval_minutes')} min\n"
            f"📝 <b>Matn:</b> <i>{html.escape(ad_text_preview)}</i>\n"
            f"🖼 <b>Rasm:</b> {'✅ Bor' if config.get('ad_photo') else '❌ Yo`q'}\n"
            f"🔄 <b>Forward:</b> {status_fwd}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📝 Matn", callback_data="admin_ad_text"),
            types.InlineKeyboardButton("📸 Rasm", callback_data="admin_ad_photo")
        )
        markup.add(
            types.InlineKeyboardButton("⏳ Interval", callback_data="admin_ad_time"),
            types.InlineKeyboardButton("🎯 Reklama guruhi", callback_data="admin_ad_target")
        )
        markup.add(
            types.InlineKeyboardButton("🚀 Hozir yuborish", callback_data="admin_ad_now")
        )
        markup.add(
            types.InlineKeyboardButton(
                f"{'🔴 Reklamani OFF' if config.get('is_ad_active') else '🟢 Reklamani ON'}",
                callback_data="admin_ad_toggle"
            ),
            types.InlineKeyboardButton(
                f"{'🔴 Forwardni OFF' if config.get('is_forwarding_active') else '🟢 Forwardni ON'}",
                callback_data="admin_fwd_toggle"
            )
        )
        bot.send_message(message.chat.id, panel_text, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('admin_'))
    def admin_callbacks(call):
        cid = call.message.chat.id
        if int(call.from_user.id) not in ADMIN_IDS:
            bot.answer_callback_query(call.id, "Siz admin emassiz!")
            return

        if call.data == "admin_ad_text":
            bot.send_message(cid, "📝 <b>Yangi reklama matnini yuboring:</b>", parse_mode="HTML")
            user_states[cid] = 'setting_ad_text'
        elif call.data == "admin_ad_photo":
            bot.send_message(cid, "📸 <b>Reklama uchun rasm yuboring (yoki 'ochir' deb yozing):</b>", parse_mode="HTML")
            user_states[cid] = 'setting_ad_photo'
        elif call.data == "admin_ad_time":
            bot.send_message(cid, "⏳ <b>Intervalni minutlarda yuboring (faqat son):</b>", parse_mode="HTML")
            user_states[cid] = 'setting_ad_time'
        elif call.data == "admin_ad_target":
            bot.send_message(cid, "🎯 <b>Reklama guruhi ID sini yuboring:</b>", parse_mode="HTML")
            user_states[cid] = 'setting_ad_target'
        elif call.data == "admin_ad_now":
            ads.send_ad(force=True)
            bot.answer_callback_query(call.id, "✅ Reklama yuborildi!")
            return
        elif call.data == "admin_ad_toggle":
            config['is_ad_active'] = not config['is_ad_active']
            save_config(config)
            ads.reschedule_ads()
            bot.answer_callback_query(call.id, "Holat o'zgardi")
            admin_panel(call.message)
            return
        elif call.data == "admin_fwd_toggle":
            config['is_forwarding_active'] = not config['is_forwarding_active']
            save_config(config)
            bot.answer_callback_query(call.id, "Forwarding holati o'zgardi")
            admin_panel(call.message)
            return

        bot.answer_callback_query(call.id)

    @bot.message_handler(func=lambda m: m.text in ["🚖 Taksi chaqirish", "📦 Pochta jo'natish"])
    def start_order(message):
        cid = message.chat.id
        order_type = 'Taksi' if "Taksi" in message.text else 'Pochta'
        user_states[cid] = {'type': order_type, 'step': 'name'}

        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ Bekor qilish"))

        bot.send_message(cid, "📝 <b>Ismingizni yozing:</b>", reply_markup=cancel_markup, parse_mode="HTML")

    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        cid = message.chat.id
        if cid in user_states and isinstance(user_states[cid], dict) and user_states[cid].get('step') == 'phone':
            phone = message.contact.phone_number
            if phone and not phone.startswith('+'):
                phone = '+' + phone
            user_states[cid]['phone'] = phone
            user_states[cid]['step'] = 'from'
            bot.send_message(cid, "📍 <b>Qayerdan?</b> (Manzilni yozing):", parse_mode="HTML")

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        cid = message.chat.id
        if not (cid in user_states and isinstance(user_states[cid], dict) and user_states[cid].get('step') == 'location'):
            return

        state = user_states[cid]
        state['lat'] = message.location.latitude
        state['lon'] = message.location.longitude

        target = config.get('destination_group')
        if not target:
            logger.error("Destination group not set in config!")
            bot.send_message(cid, "❌ Xatolik: Guruh sozlanmagan. Iltimos adminga xabar bering.")
            del user_states[cid]
            start(message)
            return

        title = "🚖 #YANGI_TAKSI" if state['type'] == 'Taksi' else "📦 #YANGI_POCHTA"
        user = message.from_user
        esc_name = html.escape(state['name'])
        
        if user.username:
            profile = f"<a href='https://t.me/{user.username}'>{esc_name}</a>"
        else:
            profile = f"<a href='tg://user?id={user.id}'>{esc_name}</a>"

        uz_time = (datetime.utcnow() + timedelta(hours=5)).strftime('%H:%M:%S')
        comment_line = f"\n💬 <b>Izoh:</b> <i>{html.escape(state['comment'])}</i>" if state.get('comment') else ""

        text = (
            f"📥 <b>{title}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Mijoz:</b> {profile}\n"
            f"📞 <b>Tel:</b> {html.escape(state['phone'])}\n"
            f"📍 <b>Qayerdan:</b> <code>{html.escape(state['from'])}</code>\n"
            f"🏁 <b>Qayerga:</b> <code>{html.escape(state['to'])}</code>"
            f"{comment_line}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🕒 <b>Vaqt:</b> <code>{uz_time}</code>"
        )

        mk_group = types.InlineKeyboardMarkup()
        mk_group.add(
            types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"order_accept_{cid}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"order_reject_{cid}")
        )
        if user.username:
            mk_group.add(types.InlineKeyboardButton("✉️ Mijozga yozish", url=f"https://t.me/{user.username}"))
        else:
            mk_group.add(types.InlineKeyboardButton("👤 Mijoz profili", url=f"tg://user?id={user.id}"))

        try:
            m = bot.send_message(target, text, parse_mode="HTML", reply_markup=mk_group)
            bot.send_location(target, state['lat'], state['lon'], reply_to_message_id=m.message_id)
            bot.send_message(cid, "✅ <b>Buyurtmangiz yuborildi!</b>\nTez orada haydovchilar bog'lanishadi. 🚗", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send order: {e}")
            bot.send_message(cid, "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")

        del user_states[cid]
        start(message)

    @bot.message_handler(func=lambda m: m.chat.id in user_states and isinstance(user_states[m.chat.id], dict))
    def order_steps(message):
        cid = message.chat.id
        state = user_states[cid]
        step = state.get('step')

        if message.text == "❌ Bekor qilish":
            del user_states[cid]
            start(message)
            return

        if step == 'name':
            state['name'] = html.escape(message.text)
            state['step'] = 'phone'
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            mk.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
            mk.add(types.KeyboardButton("❌ Bekor qilish"))
            bot.send_message(cid, "📞 <b>Telefon raqamingizni yuboring:</b>", reply_markup=mk, parse_mode="HTML")

        elif step == 'phone':
            phone = message.text.strip()
            if not phone.replace('+', '').replace(' ', '').isdigit() or len(phone) < 7:
                bot.send_message(cid, "⚠️ Iltimos, to'g'ri telefon raqam kiriting.")
                return
            state['phone'] = phone
            state['step'] = 'from'
            bot.send_message(cid, "📍 <b>Qayerdan?</b> (Manzilni yozing):", parse_mode="HTML")

        elif step == 'from':
            state['from'] = message.text
            state['step'] = 'to'
            bot.send_message(cid, "🏁 <b>Qayerga?</b> (Manzilni yozing):", parse_mode="HTML")

        elif step == 'to':
            state['to'] = message.text
            state['step'] = 'location'
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            mk.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
            mk.add(types.KeyboardButton("❌ Bekor qilish"))
            bot.send_message(cid, "🗺 <b>Lokatsiyangizni yuboring:</b>", reply_markup=mk, parse_mode="HTML")

        elif step == 'location':
            # This is handled by handle_location, but if they type text:
            bot.send_message(cid, "📍 Iltimos, pastdagi tugma orqali lokatsiyangizni yuboring.")

    @bot.message_handler(func=lambda m: m.chat.id in user_states and isinstance(user_states[m.chat.id], str))
    def handle_admin_inputs(message):
        cid = message.chat.id
        if not is_admin(message):
            return

        state = user_states[cid]

        if state == 'setting_ad_text':
            config['ad_text'] = message.text
            save_config(config)
            bot.send_message(cid, "✅ Reklama matni saqlandi.")
        elif state == 'setting_ad_photo':
            if message.content_type == 'photo':
                config['ad_photo'] = message.photo[-1].file_id
                save_config(config)
                bot.send_message(cid, "✅ Reklama rasmi saqlandi.")
            elif message.text and message.text.lower() in ['ochir', "o'chir", 'yoq', "yo'q"]:
                config['ad_photo'] = None
                save_config(config)
                bot.send_message(cid, "✅ Reklama rasmi olib tashlandi.")
            else:
                bot.send_message(cid, "Iltimos, rasm yuboring yoki 'ochir' deb yozing.")
                return
        elif state == 'setting_ad_time':
            try:
                minutes = int(message.text)
                if minutes < 1:
                    raise ValueError("Must be positive")
                config['ad_interval_minutes'] = minutes
                save_config(config)
                ads.reschedule_ads()
                bot.send_message(cid, f"✅ Interval {minutes} minutga sozlandi.")
            except ValueError:
                bot.send_message(cid, "Faqat musbat raqam yuboring.")
                return
        elif state == 'setting_ad_target':
            config['ad_target_group'] = message.text.strip()
            save_config(config)
            bot.send_message(cid, "✅ Reklama guruhi saqlandi.")
        elif state == 'setting_source':
            config['source_group'] = message.text.strip()
            save_config(config)
            bot.send_message(cid,
                "✅ Manba guruh saqlandi.\n"
                "📥 Endi <b>Qabul qiluvchi guruh</b> ID sini yuboring:",
                parse_mode="HTML")
            user_states[cid] = 'setting_destination'
            return
        elif state == 'setting_destination':
            config['destination_group'] = message.text.strip()
            save_config(config)
            bot.send_message(cid, "✅ Qabul qiluvchi guruh saqlandi.\nBot to'liq sozlandi! ✅")

        if cid in user_states:
            del user_states[cid]

    @bot.message_handler(content_types=['photo'], func=lambda m: user_states.get(m.chat.id) == 'setting_ad_photo')
    def handle_ad_photo(message):
        handle_admin_inputs(message)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('order_'))
    def order_callbacks(call):
        cid = call.message.chat.id
        data = call.data.split('_')
        # data = ['order', 'accept'/'reject', customer_id]
        action = data[1]
        customer_id = int(data[2])

        driver_name = html.escape(call.from_user.first_name or "Haydovchi")
        driver_username = f" (@{call.from_user.username})" if call.from_user.username else ""

        if action == "accept":
            try:
                # FIX: avoid parse_mode conflict by using reply_markup removal
                bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
                bot.send_message(
                    cid,
                    f"✅ <b>QABUL QILINDI</b> — {driver_name}{driver_username}",
                    parse_mode="HTML",
                    reply_to_message_id=call.message.message_id
                )
            except Exception as e:
                logger.error(f"Error editing order message: {e}")
            try:
                bot.send_message(
                    customer_id,
                    f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n"
                    f"👤 Haydovchi: <b>{driver_name}{driver_username}</b>\n"
                    "Haydovchi sizga aloqaga chiqadi. 🚗",
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify customer {customer_id}: {e}")
            bot.answer_callback_query(call.id, "✅ Buyurtma qabul qilindi")

        elif action == "reject":
            try:
                bot.edit_message_reply_markup(cid, call.message.message_id, reply_markup=None)
                bot.send_message(
                    cid,
                    f"❌ <b>RAD ETILDI</b> — {driver_name}{driver_username}",
                    parse_mode="HTML",
                    reply_to_message_id=call.message.message_id
                )
            except Exception as e:
                logger.error(f"Error editing order message: {e}")
            bot.answer_callback_query(call.id, "❌ Buyurtma rad etildi")

    @bot.message_handler(func=lambda m: True)
    @bot.channel_post_handler(func=lambda m: True)
    def catch_all(message):
        forwarder.handle_forwarding(message)

register_handlers()
