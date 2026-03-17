from bot_instance import bot
from config import config, save_config, ADMIN_ID
from logger import logger
from telebot import types
import html
import ads
import forwarder

user_states = {}

def register_handlers():
    
    @bot.message_handler(commands=['start'])
    def start(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🚖 Taksi chaqirish"), types.KeyboardButton("📦 Pochta jo'natish"))
        bot.send_message(message.chat.id, 
            f"🌟 *Assalomu alaykum, {message.from_user.first_name}!*\n\n"
            "Sizga qanday xizmat kerak? Quyidagi tugmalardan birini tanlang:", 
            reply_markup=markup, parse_mode="Markdown")

    @bot.message_handler(commands=['status'])
    def status(message):
        s = config.get('source_group', 'Sozlanmagan')
        d = config.get('destination_group', 'Sozlanmagan')
        ad_g = config.get('ad_target_group', s)
        
        status_text = (
            f"📊 *Bot holati*\n\n"
            f"📤 Manba: `{s}`\n"
            f"📥 Qabul qiluvchi: `{d}`\n"
            f"📢 Reklama guruhi: `{ad_g}`\n"
            f"🔄 Forward: {'🟢' if config.get('is_forwarding_active') else '🔴'}\n"
            f"📢 Reklama: {'🟢' if config.get('is_ad_active') else '🔴'}\n"
            f"⏳ Interval: {config.get('ad_interval_minutes')} min"
        )
        bot.send_message(message.chat.id, status_text, parse_mode="Markdown")

    @bot.message_handler(commands=['admin'], func=lambda m: str(m.from_user.id) == str(ADMIN_ID))
    def admin_panel(message):
        status_ad = "🟢 YOQILGAN" if config.get('is_ad_active') else "🔴 O'CHIRILGAN"
        status_fwd = "🟢 YOQILGAN" if config.get('is_forwarding_active') else "🔴 O'CHIRILGAN"
        
        ad_text_preview = (config.get('ad_text')[:40] + "...") if config.get('ad_text') else "Mavjud emas"
        
        panel_text = (
            f"🛠 *Admin Panel*\n\n"
            f"📢 *Reklama holati:* {status_ad}\n"
            f"⏳ *Interval:* {config.get('ad_interval_minutes')} min\n"
            f"📝 *Matn:* _{ad_text_preview}_\n"
            f"🔄 *Forward:* {status_fwd}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📝 Matn", callback_data="admin_ad_text"),
            types.InlineKeyboardButton("📸 Rasm", callback_data="admin_ad_photo")
        )
        markup.add(
            types.InlineKeyboardButton("⏳ Interval", callback_data="admin_ad_time"),
            types.InlineKeyboardButton("🎯 Guruh ID", callback_data="admin_ad_target")
        )
        markup.add(
            types.InlineKeyboardButton("🚀 Reklamani hozir yuborish", callback_data="admin_ad_now")
        )
        markup.add(
            types.InlineKeyboardButton(f"{'🔴 Reklamani o`chirish' if config.get('is_ad_active') else '🟢 Reklamani yoqish'}", callback_data="admin_ad_toggle"),
            types.InlineKeyboardButton(f"{'🔴 Forwardni o`chirish' if config.get('is_forwarding_active') else '🟢 Forwardni yoqish'}", callback_data="admin_fwd_toggle")
        )
        bot.send_message(message.chat.id, panel_text, reply_markup=markup, parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('admin_'))
    def admin_callbacks(call):
        cid = call.message.chat.id
        if call.data == "admin_ad_text":
            bot.send_message(cid, "Yangi reklama matnini yuboring:")
            user_states[cid] = 'setting_ad_text'
        elif call.data == "admin_ad_photo":
            bot.send_message(cid, "Reklama uchun rasm yuboring (yoki 'yo'q' deb yozing):")
            user_states[cid] = 'setting_ad_photo'
        elif call.data == "admin_ad_time":
            bot.send_message(cid, "Intervalni minutlarda yuboring:")
            user_states[cid] = 'setting_ad_time'
        elif call.data == "admin_ad_target":
            bot.send_message(cid, "Reklama yuborilishi kerak bo'lgan guruh ID sini yuboring:")
            user_states[cid] = 'setting_ad_target'
        elif call.data == "admin_ad_now":
            ads.send_ad()
            bot.answer_callback_query(call.id, "Reklama guruhga yuborildi!")
        elif call.data == "admin_ad_toggle":
            config['is_ad_active'] = not config['is_ad_active']
            save_config(config)
            ads.reschedule_ads()
            bot.answer_callback_query(call.id, "O'zgartirildi")
            admin_panel(call.message)
        elif call.data == "admin_fwd_toggle":
            config['is_forwarding_active'] = not config['is_forwarding_active']
            save_config(config)
            bot.answer_callback_query(call.id, "O'zgartirildi")
            admin_panel(call.message)

    @bot.message_handler(func=lambda m: m.text in ["🚖 Taksi chaqirish", "📦 Pochta jo'natish"])
    def start_order(message):
        cid = message.chat.id
        user_states[cid] = {'type': 'Taksi' if "Taksi" in message.text else 'Pochta', 'step': 'name'}
        
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ Bekor qilish"))
        
        bot.send_message(cid, "📝 *Ismingizni yozing:*", reply_markup=cancel_markup, parse_mode="Markdown")

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
            state['name'] = message.text
            state['step'] = 'phone'
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            mk.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
            bot.send_message(cid, "📞 *Telefon raqamingizni yuboring:*", reply_markup=mk, parse_mode="Markdown")
        elif step == 'phone':
            state['phone'] = message.text
            state['step'] = 'from'
            bot.send_message(cid, "📍 *Qayerdan:*", parse_mode="Markdown")
        elif step == 'from':
            state['from'] = message.text
            state['step'] = 'to'
            bot.send_message(cid, "🏁 *Qayerga:*", parse_mode="Markdown")
        elif step == 'to':
            state['to'] = message.text
            state['step'] = 'location'
            mk = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            mk.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
            mk.add(types.KeyboardButton("❌ Bekor qilish"))
            bot.send_message(cid, "🗺 *Lokatsiyangizni yuboring:*", reply_markup=mk, parse_mode="Markdown")

    @bot.message_handler(content_types=['contact'])
    def handle_contact(message):
        cid = message.chat.id
        if cid in user_states and isinstance(user_states[cid], dict) and user_states[cid].get('step') == 'phone':
            user_states[cid]['phone'] = message.contact.phone_number
            user_states[cid]['step'] = 'from'
            bot.send_message(cid, "📍 Qayerdan?")

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        cid = message.chat.id
        if cid in user_states and isinstance(user_states[cid], dict) and user_states[cid].get('step') == 'location':
            state = user_states[cid]
            state['lat'] = message.location.latitude
            state['lon'] = message.location.longitude
            
            target = config.get('destination_group')
            if target:
                title = "🚖 #YANGI_TAKSI" if state['type'] == 'Taksi' else "📦 #YANGI_POCHTA"
                esc_name = html.escape(state['name'])
                profile = f"<a href='tg://user?id={cid}'>{esc_name}</a>"
                
                from datetime import datetime, timedelta
                uz_time = (datetime.utcnow() + timedelta(hours=5)).strftime('%H:%M:%S')
                
                esc_from = html.escape(state['from'])
                esc_to = html.escape(state['to'])
                
                text = (f"📥 <b>{title}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"👤 <b>Mijoz:</b> {profile}\n"
                        f"📞 <b>Tel:</b> +{state['phone']}\n"
                        f"📍 <b>Qayerdan:</b> <code>{esc_from}</code>\n"
                        f"🏁 <b>Qayerga:</b> <code>{esc_to}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"🕒 <b>Vaqt:</b> <code>{uz_time}</code>")
                
                mk_group = types.InlineKeyboardMarkup()
                mk_group.add(
                    types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"order_accept_{cid}"),
                    types.InlineKeyboardButton("❌ Rad etish", callback_data=f"order_reject_{cid}")
                )

                m = bot.send_message(target, text, parse_mode="HTML", reply_markup=mk_group)
                bot.send_location(target, state['lat'], state['lon'], reply_to_message_id=m.message_id)
                bot.send_message(cid, "✅ *Buyurtmangiz yuborildi!*", parse_mode="Markdown")
            else:
                bot.send_message(cid, "❌ Xatolik: Guruh sozlanmagan.")
            
            del user_states[cid]
            start(message)

    @bot.message_handler(func=lambda m: m.chat.id in user_states and isinstance(user_states[m.chat.id], str))
    def handle_admin_inputs(message):
        cid = message.chat.id
        state = user_states[cid]
        
        if state == 'setting_ad_text':
            config['ad_text'] = message.text
            save_config(config)
            bot.send_message(cid, "✅ Reklama matni saqlandi.")
        elif state == 'setting_ad_time':
            try:
                config['ad_interval_minutes'] = int(message.text)
                save_config(config)
                ads.reschedule_ads()
                bot.send_message(cid, f"✅ Interval {message.text} minutga sozlandi.")
            except:
                bot.send_message(cid, "Faqat raqam yuboring.")
        elif state == 'setting_ad_target':
            config['ad_target_group'] = message.text
            save_config(config)
            bot.send_message(cid, "✅ Reklama guruhi saqlandi.")
        
        if cid in user_states: del user_states[cid]

    @bot.callback_query_handler(func=lambda c: c.data.startswith('order_'))
    def order_callbacks(call):
        cid = call.message.chat.id
        data = call.data.split('_')
        action = data[1]
        customer_id = data[2]
        
        if action == "accept":
            bot.edit_message_text(f"✅ <b>QABUL QILINDI</b>\n\n{call.message.text}", cid, call.message.message_id, parse_mode="HTML")
            bot.send_message(customer_id, "✅ <b>Buyurtmangiz qabul qilindi!</b>", parse_mode="HTML")
            bot.answer_callback_query(call.id, "Qabul qilindi")
        elif action == "reject":
            bot.edit_message_text(f"❌ <b>RAD ETILDI</b>\n\n{call.message.text}", cid, call.message.message_id, parse_mode="HTML")
            bot.answer_callback_query(call.id, "Rad etildi")

    @bot.message_handler(func=lambda m: True)
    @bot.channel_post_handler(func=lambda m: True)
    def catch_all(message):
        forwarder.handle_forwarding(message)

register_handlers()
