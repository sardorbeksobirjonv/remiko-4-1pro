import asyncio
import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.error import TelegramError
import html
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# ===== CONFIG =====
# Bot tokeningizni kiriting
TOKEN = "8528647202:AAHrcOe4Zg6lAaxQweqxiVqljXMuqsD6da8"

# ===== States =====
TIL, MINTQA, MENU, BOLM, LINK, MATN, VAQT, TAKROR, OLDINDAN, TAHRIR, EXIT_EDIT, YORDAM = range(12)

# ===== Database (Memory) =====
users = {}
tasks = {}

# ===== Static Data =====
ZONE_MAP = {
    # 🇺🇿 O‘zbekiston
    "toshkent": "Asia/Tashkent",
    "ташкент": "Asia/Tashkent",
    "uzbekistan": "Asia/Tashkent",
    "узбекистан": "Asia/Tashkent",
    "samarqand": "Asia/Tashkent",
    "самарканд": "Asia/Tashkent",
    "andijon": "Asia/Tashkent",
    "андижан": "Asia/Tashkent",

    # 🇷🇺 Rossiya
    "rossiya": "Europe/Moscow",
    "russia": "Europe/Moscow",
    "россия": "Europe/Moscow",
    "moskva": "Europe/Moscow",
    "москва": "Europe/Moscow",
    "sankt-peterburg": "Europe/Moscow",
    "питер": "Europe/Moscow",

    # 🇺🇸 AQSH
    "new york": "America/New_York",
    "newyork": "America/New_York",
    "ny": "America/New_York",
    "нью-йорк": "America/New_York",
    "washington": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",

    # 🇬🇧 Buyuk Britaniya
    "london": "Europe/London",
    "londan": "Europe/London",
    "лондон": "Europe/London",
    "uk": "Europe/London",

    # 🇹🇷 Turkiya
    "istanbul": "Europe/Istanbul",
    "istanbol": "Europe/Istanbul",
    "истамбул": "Europe/Istanbul",
    "turkiya": "Europe/Istanbul",

    # 🇩🇪 Germaniya
    "berlin": "Europe/Berlin",
    "берлин": "Europe/Berlin",
    "germany": "Europe/Berlin",

    # 🇫🇷 Fransiya
    "parij": "Europe/Paris",
    "paris": "Europe/Paris",
    "париж": "Europe/Paris",

    # 🇨🇳 Xitoy
    "beijing": "Asia/Shanghai",
    "pekin": "Asia/Shanghai",
    "пекин": "Asia/Shanghai",
    "china": "Asia/Shanghai",

    # 🇯🇵 Yaponiya
    "tokyo": "Asia/Tokyo",
    "tokio": "Asia/Tokyo",
    "токио": "Asia/Tokyo",

    # 🇰🇷 Janubiy Koreya
    "seoul": "Asia/Seoul",
    "seul": "Asia/Seoul",
    "сеул": "Asia/Seoul",

    # 🇦🇪 BAA
    "dubai": "Asia/Dubai",
    "дубай": "Asia/Dubai",
    "uae": "Asia/Dubai"
}

STRINGS = {
    "UZ": {
        "start": "🌍 Tilni tanlang / Выберите язык",
        "ask_tz": "🕙 Endi esa vaqt mintaqasini o‘rnating!\n\n✍️ O‘z vaqtingizga mos keladigan shahar nomini yuboring.\n\nMisol uchun: Toshkent",
        "menu": "<b>📌 Asosiy menyu!</b>\n\nKerakli bo‘limni tanlang 👇\n\n➕ <b>Eslatma qo‘shish</b> — yangi eslatma yarating va vaqtini belgilang\n\n📋 <b>Eslatmalar ro‘yxati</b> — barcha eslatmalarni ko‘rish va tahrirlash\n\n📖 <b>Qo‘llanma va yordam</b> — botdan foydalanish bo‘yicha yo‘riqnoma",
        "btn_new": "➕ Eslatma qo'shish",
        "btn_list": "📋 Eslatmalar ro'yxati",
        "btn_back": "⬅️ Orqaga",
        "ask_bolm": "🔔 <b>Eslatma turini tanlang!</b>\n\nIltimos, quyidagi variantlardan birini tanlang:\n\n👤 <b>Shaxsiy</b> — eslatma faqat sizga keladi\n\n👥 <b>Guruh</b> — eslatma guruhlarda keladi\n\n📢 <b>Kanal</b> — eslatma kanallarda keladi",
        "ask_link": "🔗 <b>{}</b> uchun <b>ID</b> yoki <b>Linkni</b> kiriting:\n\n⚠️ <b>DIQQAT:</b> Botni kanal/guruhga <b>ADMIN</b> qiling, aks holda xabar yubora olmaydi!",
         "ask_text": "📝 <b>Eslatma matnini kiriting.</b>\n\nMasalan:\n— Hisobotni topshirish;\n— Do'stimning tug'ilgan kuni bilan tabriklash;\n— Har 3 oyda tish schetkalarni almashtirish;\nva hokazo...",
        "ask_time": "⏰ <b>⏳ Eslatma vaqtini kiriting</b>\n\nFormat: 01.01.2026 14:00):",
         "ask_rep": "🔁 <b>Eslatma takrorlansinmi?</b>\n\nMasalan:\n— Har kuni\n— Har hafta\n— Har oy\nva hokazo...",
        "ask_pre": "⏰ <b>Oldindan eslatilsinmi?</b>\n\nMasalan:\n— 5 daqiqa oldin\n— 1 soat oldin\n— 1 kun oldin\nva hokazo...\n\n1 d = 1 daqiqa\n1 s = 1 soat\n1 k = 1 kun",
        "error_tz": "⚠️ <b>Mintaqa topilmadi</b>, Toshkent vaqti o'rnatildi.",
        "error_time": "❌ <b>Vaqt o'tmishda yoki noto'g'ri!</b>",
        "success": "✅ <b>Eslatma muvaffaqiyatli o'rnatildi!</b>",
        "no_rem": "📭 Bu bo'limda eslatmalar yo'q.",
        "btn_edit_text": "📝 Matn",
        "btn_edit_time": "⏰ Vaqt",
        "btn_edit_rep": "🔁 Takrorlash",
        "btn_edit_pre": "🔔 Oldindan",
        "btn_toggle": "🚫 Yoqish/O'chirish",
        "btn_del": "🗑 O'chirish",
        "status_on": "<b>✅ Yoqilgan</b>",
        "status_off": "<b>💤 O'chirilgan</b>",
        "btn_personal": "👤 Shaxsiy",
        "btn_group": "👥 Guruh",
        "btn_channel": "📢 Kanal",
        "ask_list_bolm": "📋 Eslatmalar ro‘yxati!\n\nAvval eslatma turini tanlang:👇",  
        "section": "<b>Bo'lim</b>",
        "location": "<b>Manzil</b>",
        "text": "<b>Matn</b>",
        "time": "<b>Vaqt</b>",
        "repeat": "<b>Takror</b>",
        "pre_rem": "<b>Oldindan</b>",
        "status": "<b>Holat</b>",
        "btn_help": "📖 Qo'llanma va yordam",
        "help_text": "🔗 Havola orqali kanalga o‘tib video-qo‘llanmalarni ko‘rishingiz mumkin👇\n\nhttps://t.me/+UFffYEZkqt02NzEy\n\nAgar sizda yana savollar bo‘lsa, bot administratori  @iam_mkhmmd ga murojaat qiling. 🧑‍💻"
    },
        "RU": {
            "start": "🌐 <b>Выберите язык:</b>",
            "ask_tz": "🕙 Теперь установите часовой пояс!\n\n✍️ Отправьте название города, соответствующего вашему времени.\n\nНапример: Ташкент",
            "menu": "<b>📌 Главное меню!</b>\n\nВыберите нужный раздел 👇\n\n➕ <b>Добавить напоминание</b> — создайте новое и укажите время\n\n📋 <b>Список напоминаний</b> — просмотр и редактирование\n\n📖 <b>Инструкция</b> — руководство по использованию",
            "btn_new": "➕ Добавить напоминание",
            "btn_list": "📋 Список напоминаний",
            "btn_back": "⬅️ Назад",
            "ask_bolm": "🔔 <b>Выберите тип напоминания!</b>\n\n👤 <b>Личное</b> — придёт только вам\n\n👥 <b>Группа</b> — придёт в группах\n\n📢 <b>Канал</b> — придёт в каналах",
            "ask_link": "🔗 Введите <b>ID</b> или <b>ссылку</b> для <b>{}</b>:\n\n⚠️ <b>ВНИМАНИЕ:</b> Сделайте бота <b>АДМИНИСТРАТОРОМ</b>!",
            "ask_text": "📝 <b>Введите текст напоминания.</b>\n\nНапример:\n— Сдать отчёт;\n— Поздравить друга с днём рождения;\n— Менять зубную щётку каждые 3 месяца;\nи т.д.",
            "ask_time": "⏳ Введите время напоминания.\n\nФормат: 01.01.2026 14:00",
            "ask_rep": "🔁 <b>Повторять напоминание?</b>\n\nНапример:\n— Каждый день\n— Каждую неделю\n— Каждый месяц\nи т.д.",
             "ask_pre": "⏰ <b>Напомнить заранее?</b>\n\nНапример:\n— за 5 минут\n— за 1 час\n— за 1 день\nи т.д.\n\n1 м = 1 минута\n1 ч = 1 час\n1 д = 1 день",
            "error_tz": "⚠️ <b>Регион не найден</b>, установлено время Ташкента.",
            "error_time": "❌ <b>Время указано неверно или находится в прошлом!</b>",
            "success": "✅ <b>Напоминание успешно установлено!</b>",
            "no_rem": "📭 В этом разделе нет напоминаний.",
            "btn_edit_text": "📝 Текст",
            "btn_edit_time": "⏰ Время",
            "btn_edit_rep": "🔁 Повтор",
            "btn_edit_pre": "🔔 Заранее",
            "btn_toggle": "🚫 Включить/Выключить",
            "btn_del": "🗑 Удалить",
            "status_on": "<b>✅ Включено</b>",
            "status_off": "<b>💤 Выключено</b>",
            "btn_personal": "👤 Личное",
            "btn_group": "👥 Группа",
            "btn_channel": "📢 Канал",
            "ask_list_bolm": "📋 <b>Список напоминаний!</b>\n\nВыберите нужный раздел 👇",
            "section": "<b>Раздел</b>",
            "location": "<b>Место</b>",
            "text": "<b>Текст</b>",
            "time": "<b>Время</b>",
            "repeat": "<b>Повтор</b>",
            "pre_rem": "<b>Заранее</b>",
            "status": "<b>Статус</b>",
            "btn_help": "📖 Инструкция и помощь",
            "help_text": "🔗 Вы можете посмотреть видеоинструкции на нашем канале, перейдя по ссылке.👇\n\nhttps://t.me/+p4L7bdZr0asxODVi\n\nЕсли у вас остались ещё вопросы, обращайтесь к администратору бота @iam_mkhmmd 🧑‍💻"
        }
}
# ===== Keyboards =====
def get_rep_kb(uid):
    """Takrorlash tugmalari - to'g'ri yozilgan"""
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["Hech qachon", "Har kuni"],
            ["Har hafta", "Har 2 hafta"],
            ["Har oy", "Choraklik (Har 3 oy)"],
            ["Har 6 oy", "Har yili"],
            ["✍️ Qo'lda"]
        ]
    else:  # RU
        return [
            ["Никогда", "Каждый день"],
            ["Каждую неделю", "Каждые 2 недели"],
            ["Каждый месяц", "Каждые 3 месяца"],
            ["Каждые 6 месяцев", "Каждый год"],
            ["✍️ Вручную"]
        ]

# ❌ ESKI (async bo'lsa ham hech qilmaydi)
# async def get_pre_kb(uid):

# ✅ YANGI (oddiy funksiya)
def get_pre_kb(uid):
    """Oldindan eslatma tugmalari"""
    lang = users.get(uid, {}).get("lang", "UZ")
    if lang == "UZ":
        return [
            ["❌ Yo'q", "1 d", "5 d"],
            ["10 d", "15 d", "30 d"],
            ["1 s", "2 s", "3 s"],
            ["6 s", "12 s"],
            ["1 k", "2 k", "3 k"],
            ["7 k", "14 k", "✍️ Qo'lda"]
        ]
    else:  # RU
        return [
            ["❌ Нет", "1 м", "5 м"],
            ["10 м", "15 м", "30 м"],
            ["1 ч", "2 ч", "3 ч"],
            ["6 ч", "12 ч"],
            ["1 д", "2 д", "3 д"],
            ["7 д", "14 д", "✍️ Вручную"]
        ]


# ===== Helpers =====
def get_s(uid, key):
    lang = users.get(uid, {}).get("lang", "UZ")
    return STRINGS[lang].get(key, key)

def parse_duration(text):
    text = text.lower().strip()
    match = re.search(r"(\d+)", text)
    if not match: return None
    val = int(match.group(1))
    if any(x in text for x in ["kun", "день", "d"]): return timedelta(days=val)
    if any(x in text for x in ["soat", "час", "h", "s"]): return timedelta(hours=val)
    if any(x in text for x in ["daqiqa", "мин", "m", "d"]): return timedelta(minutes=val)
    if any(x in text for x in ["hafta", "недел", "w"]): return timedelta(weeks=val)
    return None

# Qo'shilgan helper: foydalanuvchi yozuvi borligini kafolatlaydi
def ensure_user(uid):
    if uid not in users:
        users[uid] = {"reminders": [], "lang": "UZ", "tz": ZoneInfo("Asia/Tashkent")}
# ...existing code...

# ...existing code...
def _human_repeat_label(uid, td):
    """Return localized, human-friendly repeat label for timedelta td."""
    lang = users.get(uid, {}).get("lang", "UZ")
    if td is None:
        return "Yo'q" if lang == "UZ" else "Никогда"

    secs = int(td.total_seconds())
    days = secs // 86400

    common = {
        "UZ": {
            1: "🔄 Har kuni",
            7: "📅 Har hafta",
            14: "🗓 Har 2 haftada",
            30: "Har oy",
            90: "3 oyda",
            180: "6 oyda",
            365: "Har yili",
        },
        "RU": {
            1: "🔄 Каждый день",
            7: "📅 Каждую неделю",
            14: "🗓 Каждые 2 недели",
            30: "Каждый месяц",
            90: "Каждые 3 месяца",
            180: "Каждые 6 месяцев",
            365: "Каждый год",
        },
    }

    if days in common.get(lang, {}):
        return common[lang][days]

    # Fallback: show in largest whole unit
    if secs % 86400 == 0:
        return (f"{days} {'kun' if lang == 'UZ' else 'дней'}") if days > 1 else ( "1 kun" if lang=="UZ" else "1 день")
    hours = secs // 3600
    if secs % 3600 == 0 and hours > 0:
        return f"{hours} {'soat' if lang == 'UZ' else 'час(а)'}"
    minutes = secs // 60
    return f"{minutes} {'daqiqa' if lang == 'UZ' else 'минут(ы)'}"

def _human_pre_label(uid, minutes):
    """Return localized pre-reminder label (e.g. '5 daqiqa oldin' / 'за 5 минут')."""
    lang = users.get(uid, {}).get("lang", "UZ")
    if not minutes:
        return "Yo'q" if lang == "UZ" else "Нет"
    if minutes < 60:
        return f"{minutes} daqiqa oldin" if lang == "UZ" else f"за {minutes} минут"
    if minutes % 60 == 0 and minutes // 60 < 24:
        hrs = minutes // 60
        return f"{hrs} soat oldin" if lang == "UZ" else f"за {hrs} час(а)"
    days = minutes // 1440
    return f"{days} kun oldin" if lang == "UZ" else f"за {days} день(дней)"

def format_reminder_text(uid, r):
    """
    Format reminder display:
    - labels from STRINGS (they already contain <b>...</b>)
    - values are HTML-escaped and shown in italics (<i>...</i>)
    - localized repeat / pre-reminder strings
    """
    lang = users.get(uid, {}).get("lang", "UZ")

    # status (use existing STRINGS HTML snippets for consistency)
    status_html = STRINGS[lang]["status_on"] if r.get("is_active") else STRINGS[lang]["status_off"]

    # user text (escaped) shown in italic
    text_val = html.escape(r.get("text", "")) or ("—" if lang == "UZ" else "—")

    # time formatted using user's tz already stored in r['time']
    time_val = r.get("time")
    if time_val:
        # use language-agnostic datetime format, but you can tweak per lang if needed
        time_str = time_val.strftime("%d.%m.%Y %H:%M")
    else:
        time_str = "—"

    # repeat and pre labels
    rep_label = _human_repeat_label(uid, r.get("repeat"))
    pre_label = _human_pre_label(uid, r.get("pre_rem", 0))

    # final localized footer instruction
    footer = ("Eslatmani yoqish yoki o'chirish uchun pastdagi tugmani bosing 👇"
              if lang == "UZ"
              else "Чтобы включить или отключить напоминание, нажмите кнопку ниже 👇")

    # Build HTML text: labels are taken from STRINGS and values are italicized
    text = (
        f"🔔 {STRINGS[lang].get('status')}\n— {status_html}\n\n"
        f"📝 {STRINGS[lang].get('text')}\n— <i>{text_val}</i>\n\n"
        f"⏰ {STRINGS[lang].get('time')}\n— <i>{html.escape(time_str)}</i>\n\n"
        f"🔁 {STRINGS[lang].get('repeat')}\n— <i>{html.escape(rep_label)}</i>\n\n"
        f"⏰ {STRINGS[lang].get('pre_rem')}\n— <i>{html.escape(pre_label)}</i>\n\n"
        f"{footer}"
    )
    return text
# ...existing code...

# ===== CORE FUNCTIONS =====
async def send_reminder(context, uid, target, msg_type, r):
    """Xabar yuborish — TIL-SEZUVCHAN ✅"""
    try:
        lang = users.get(uid, {}).get("lang", "UZ")
        
        # Xabar shablonlari
        if msg_type == "PRE":
            msg = (
                f"🔔 OLDINDAN ESLATMA ({r['pre_rem']} min qoldi):\n\n{r['text']}"
                if lang == "UZ"
                else f"🔔 ЗАРАНЕЕ НАПОМИНАНИЕ ({r['pre_rem']} мин осталось):\n\n{r['text']}"
            )
        else:  # MAIN
            msg = (
                f"⏰ VAQTI BO'LDI:\n\n{r['text']}"
                if lang == "UZ"
                else f"⏰ ВРЕМЯ ПРИШЛО:\n\n{r['text']}"
            )
        
        await context.bot.send_message(chat_id=target, text=msg)
        return True
    except TelegramError as e:
        print(f"Xatolik ({target}): {e}")
        return False


async def reminder_scheduler(uid, r, context):
    pre_sent = False
    tz = r["time"].tzinfo

    while True:
        try:
            if r["id"] not in [x["id"] for x in users.get(uid, {}).get("reminders", [])]:
                break

            now = datetime.now(tz)

            if r.get("bolm") == get_s(uid, "btn_personal"):
                target_chat = uid
            else:
                target_chat = r.get("link", uid)

            # 🔔 OLDINDAN eslatma
            if r.get("pre_rem", 0) > 0 and not pre_sent:
                if now >= (r["time"] - timedelta(minutes=r["pre_rem"])):
                    if r.get("is_active", True):
                        await send_reminder(context, uid, target_chat, "PRE", r)  # 👈 uid qo'shildi
                    pre_sent = True

            # ⏰ Asosiy vaqt
            if now >= r["time"]:
                if r.get("is_active", True):
                    await send_reminder(context, uid, target_chat, "MAIN", r)  # 👈 uid qo'shildi

                if r.get("repeat"):
                    r["time"] += r["repeat"]
                    pre_sent = False
                    continue
                else:
                    r["is_active"] = False
                    break

            await asyncio.sleep(20)

        except Exception as e:
            print("Scheduler xato:", e)
            await asyncio.sleep(60)

async def reschedule_task(uid, r, context):
    if uid in tasks and r["id"] in tasks[uid]:
        tasks[uid][r["id"]].cancel()
    if uid not in tasks: tasks[uid] = {}
    tasks[uid][r["id"]] = asyncio.create_task(reminder_scheduler(uid, r, context))

# ===== HANDLERS =====
async def send(update, text, kb=None):
    """
    Universal yuborish funksiyasi.
    HTML (bold) avtomatik ishlaydi.
    """
    await update.message.reply_text(
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # Agar foydalanuvchi oldin ro'yxatdan o'tgan bo'lsa
    if uid in users and users[uid].get("lang") and users[uid].get("tz"):
        # To'g'ridan-to'g'ri asosiy menyuga o'tish
        return await menu_display(update, context)
    
    # Agar yangi foydalanuvchi bo'lsa — tilni tanlash
    if uid not in users:
        users[uid] = {"reminders": [], "lang": "UZ", "tz": ZoneInfo("Asia/Tashkent")}
    
    kb = [["🇺🇿 O'zbekcha", "🇷🇺 Русский"]]
    await send(
        update,
        get_s(uid, "start"),
        ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return TIL

async def go_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users[uid].pop("current", None)
    users[uid].pop("edit_target", None)
    users[uid].pop("list_bolm", None)
    users[uid].pop("list_link", None)
    users[uid].pop("target_map", None)
    return await menu_display(update, context)

async def change_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }

    kb = [["🇺🇿 O‘zbekcha", "🇷🇺 Русский"]]

    await send(
        update,
        get_s(uid, "start"),
        ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return TIL

async def set_time_zone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }

    await send(
        update,
        get_s(uid, "ask_tz"),
        ReplyKeyboardRemove()
    )
    return MINTQA

async def til_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if "Рус" in text or "🇷🇺" in text:
        users[uid]["lang"] = "RU"
    else:
        users[uid]["lang"] = "UZ"

    await send(
        update,
        get_s(uid, "ask_tz"),
        ReplyKeyboardRemove()
    )
    return MINTQA

async def mintqa_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.lower().strip()

    zone = None
    for k, v in ZONE_MAP.items():
        if k in text:
            zone = v
            break

    if not zone:
        await send(
            update,
            "❌ <b>Mintaqa topilmadi!</b>\n\n"
            "👉 <b>Faqat shularni kiriting:</b>\n"
            "• Toshkent\n"
            "• Rossiya\n"
            "• New York\n\n"
            "📝 Ruscha yoki lotincha yozish mumkin"
        )
        return MINTQA

    users[uid]["tz"] = ZoneInfo(zone)
    return await menu_display(update, context)


async def menu_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    
    # Asosiy menyu tugmalari
    kb = [
        [get_s(uid, "btn_new")],
        [get_s(uid, "btn_list")],
        [get_s(uid, "btn_help")]
    ]

    # Menu matni (bold ishlashi uchun STRINGS ichida <b>...</b> qo‘shilgan bo‘lishi kerak)
    await send(
        update, 
        get_s(uid, "menu"), 
        ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )
    return MENU


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    # 🔙 Orqaga → asosiy menyu
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    # ➕ Yangi eslatma
    if text == get_s(uid, "btn_new"):
        users[uid]["current"] = {
            "is_active": True,
            "id": str(uuid.uuid4())
        }

        kb = [
            [get_s(uid, "btn_personal")],
            [get_s(uid, "btn_group")],
            [get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        # HTML bold ishlashi uchun send 
        # idan foydalanamiz
        await send(
            update,
            get_s(uid, "ask_bolm"),  # STRINGS ichida <b>...</b> qo‘yilgan bo‘lishi kerak
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return BOLM

    # 📋 Ro‘yxatlar
    elif text == get_s(uid, "btn_list"):
        # Har bir bo'lim tugmasi alohida qatorda bo'lishi uchun
        kb = [
            [get_s(uid, "btn_personal")],
            [get_s(uid, "btn_group")],
            [get_s(uid, "btn_channel")],
            [get_s(uid, "btn_back")]
        ]

        await send(  # Yana send helperidan foydalanamiz
            update,
            get_s(uid, "ask_list_bolm"),  # STRINGS ichida <b>...</b> qo‘yish mumkin
            ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR

    # 📖 Qo'llanma va yordam
    elif text == get_s(uid, "btn_help"):
        return await yordam_handler(update, context)

    return MENU
# ...existing code...
async def yordam_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.idortga
    await send(
        update,
        get_s(uid, "help_text"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return MENU
# ...existing code...

async def bolm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    val = update.message.text

    # 🔙 Orqaga bosilgan bo‘lsa, asosiy menyuga qaytish
    if val == get_s(uid, "btn_back"):
        return await menu_display(update, context)

    # Foydalanuvchi joriy bo‘limini saqlash
    users.setdefault(uid, {}).setdefault("current", {})["bolm"] = val

    # Shaxsiy bo'lim
    if val == get_s(uid, "btn_personal"):
        users[uid]["current"]["link"] = uid  # ✅ FIX: Add link for personal
        await send(
            update,
            get_s(uid, "ask_text"),  # STRINGS ichida <b>...</b> bo‘lishi kerak
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return MATN

    # Guruh yoki Kanal bo‘limlari
    if val in [get_s(uid, "btn_group"), get_s(uid, "btn_channel")]:
        await send(
            update,
            get_s(uid, "ask_link").format(val),  # <b>...</b> qo‘shish mumkin
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return LINK

    # Agar boshqa xato kiritsa, menu qaytaradi
    return await menu_display(update, context)


def normalize_chat_id(text: str):
    """
    Foydalanuvchidan kiritilgan chat ID'ni to‘g‘rilaydi:
    - To‘liq superguruh / kanal ID (-100 bilan boshlanuvchi)
    - Qisqa manfiy ID → -100 bilan to‘g‘rilash
    - Noto‘g‘ri format → None
    """
    text = text.strip()

    if text.startswith("-100") and text[4:].isdigit():
        return int(text)

    if text.startswith("-") and text[1:].isdigit():
        return int("-100" + text[1:])

    return None

async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    target = normalize_chat_id(text)

    if not target and "t.me/" in text:
        username = text.split("t.me/")[-1].replace("/", "")
        target = "@" + username

    if not target and text.startswith("@"):
        target = text

    if not target:
        await send(
            update,
            "❌ <b>Noto‘g‘ri format!</b>\n\n"
            "🔒 <b>Maxfiy kanal / guruh:</b>\n-1001234567890\n\n"
            "📢 <b>Ochiq kanal:</b>\n@kanal_nomi",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return LINK

    users[uid]["current"]["link"] = target

    await send(
        update,
        get_s(uid, "ask_text"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )
    return MATN

async def matn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    target = users[uid].get("edit_target", users[uid]["current"])
    target["text"] = text

    if "edit_target" in users[uid]:
        return await tahrir_item_display(update, context)

    await send(update, get_s(uid, "ask_time"))
    return VAQT

async def vaqt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if uid not in users:
        users[uid] = {
            "reminders": [],
            "lang": "UZ",
            "tz": ZoneInfo("Asia/Tashkent")
        }
        return await start(update, context)

    target = users[uid].get("edit_target") or users[uid].get("current")
    if not target:
        return await menu_display(update, context)

    tz = users[uid].get("tz", ZoneInfo("Asia/Tashkent"))
    text = update.message.text.strip()

    try:
        # ⏰ Sana va vaqtni parse qilish
        if ":" in text:
            dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
        else:
            dt = datetime.strptime(text, "%d.%m.%Y").replace(hour=9, minute=0)

        dt = dt.replace(tzinfo=tz)
        now = datetime.now(tz)

        # ❌ O‘tmish vaqt
        if dt < now:
            await send(
                update,
                get_s(uid, "error_time"),
                ReplyKeyboardMarkup(
                    [[get_s(uid, "btn_back")]],
                    resize_keyboard=True
                )
            )
            return VAQT

        target["time"] = dt

        # ✏️ Tahrirlash rejimi
        if "edit_target" in users[uid]:
            await reschedule_task(uid, target, context)
            return await tahrir_item_display(update, context)

        # 🔁 Takrorlashni so‘rash
        await send(
            update,
            get_s(uid, "ask_rep"),
            ReplyKeyboardMarkup(
                get_rep_kb(uid) + [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return TAKROR

    except ValueError:
        await send(
            update,
            get_s(uid, "error_time"),
            ReplyKeyboardMarkup(
                [[get_s(uid, "btn_back")]],
                resize_keyboard=True
            )
        )
        return VAQT

# python
async def takror_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    td = None
    lang = users[uid]["lang"]

    rep_map = {
        "UZ": {
            "Hech qachon": None,
            "Har kuni": timedelta(days=1),
            "Har hafta": timedelta(weeks=1),
            "Har 2 hafta": timedelta(weeks=2),
            "Har oy": timedelta(days=30),
            "Choraklik (Har 3 oy)": timedelta(days=90),
            "Har 6 oy": timedelta(days=180),
            "Har yili": timedelta(days=365),
        },
        "RU": {
            "Никогда": None,
            "Каждый день": timedelta(days=1),
            "Каждую неделю": timedelta(weeks=1),
            "Каждые 2 недели": timedelta(weeks=2),
            "Каждый месяц": timedelta(days=30),
            "Каждые 3 месяца": timedelta(days=90),
            "Каждые 6 месяцев": timedelta(days=180),
            "Каждый год": timedelta(days=365),
        }
    }

    # 1️⃣ Tugmalar bo'yicha matching (emoji yo'q)
    for k, v in rep_map.get(lang, {}).items():
        if k == text:
            td = v
            break

    # 2️⃣ Qo'lda kiritish
    if td is None and (("Qo'lda" in text) or ("Вручную" in text)):
        await send(
            update,
            "✍️ Masalan: 2 kun, 5 soat yoki 1 hafta:"
            if lang == "UZ"
            else "✍️ Например: 2 дня, 5 часов или 1 неделя:",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return TAKROR

    # 3️⃣ Erkin parsing
    if td is None:
        td = parse_duration(text)

    target = users[uid].get("edit_target", users[uid]["current"])
    target["repeat"] = td

    # 4️⃣ Tahrirlash rejimi
    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    # 5️⃣ Yangi eslatma — oldindan eslatmasini so'rash
    # ✅ await chiqarish (get_pre_kb oddiy funksiya)
    await send(
        update,
        get_s(uid, "ask_pre"),
        ReplyKeyboardMarkup(
            get_pre_kb(uid) + [[get_s(uid, "btn_back")]],
            resize_keyboard=True
        )
    )
    return OLDINDAN


async def oldindan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oldindan eslatma vaqti - barcha variantlarni qabul qiladi"""
    uid = update.effective_user.id
    text = update.message.text.strip()
    lang = users[uid]["lang"]
    pre = None

    # ❌ ORQAGA tugmasi
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    # 1️⃣ "Yo'q" / "Нет" - eslatma yoq
    if text in ["❌ Yo'q", "❌ Нет"]:
        pre = 0

    # 2️⃣ DAQIQALAR (d / м)
    elif text.endswith(("d", "м")):
        match = re.search(r"(\d+)", text)
        if match:
            n = int(match.group(1))
            pre = n  # Daqiqalarda saqla

    # 3️⃣ SOATLAR (s / ч)
    elif text.endswith(("s", "ч")):
        match = re.search(r"(\d+)", text)
        if match:
            n = int(match.group(1))
            pre = n * 60  # Soatni daqiqalarga aylandir

    # 4️⃣ KUNLAR (k / д)
    elif text.endswith(("k", "д")):
        match = re.search(r"(\d+)", text)
        if match:
            n = int(match.group(1))
            pre = n * 1440  # Kunni daqiqalarga aylandir

    # 5️⃣ QOLDA KIRITISH
    elif "Qo'lda" in text or "Вручную" in text:
        await send(
            update,
            "✍️ Masalan: 10d, 1s, 2k yoki 15 daqiqa:"
            if lang == "UZ"
            else "✍️ Например: 10м, 1ч, 2д или 15 минут:",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return OLDINDAN

    # 6️⃣ ERKIN MATN (masalan: "15 daqiqa", "2 soat", "3 kun")
    else:
        nums = re.findall(r"\d+", text)
        if not nums:
            await send(
                update,
                "❌ <b>Vaqt topilmadi!</b>" if lang == "UZ" else "❌ <b>Время не найдено!</b>",
                ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
            )
            return OLDINDAN

        n = int(nums[0])

        # Birliklarni aniqlash
        if lang == "UZ":
            if any(x in text.lower() for x in ["daqiqa", "min", "d"]):
                pre = n
            elif any(x in text.lower() for x in ["soat", "s"]):
                pre = n * 60
            elif any(x in text.lower() for x in ["kun", "k"]):
                pre = n * 1440
        else:  # RU
            if any(x in text.lower() for x in ["мин", "м"]):
                pre = n
            elif any(x in text.lower() for x in ["час", "ч"]):
                pre = n * 60
            elif any(x in text.lower() for x in ["день", "д"]):
                pre = n * 1440

    # ❌ Agar pre hali None bo'lsa - xato
    if pre is None or pre < 0:
        await send(
            update,
            "❌ <b>Vaqt topilmadi!</b>" if lang == "UZ" else "❌ <b>Время не найдено!</b>",
            ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
        )
        return OLDINDAN

    # ✅ SAQLASH
    target = users[uid].get("edit_target", users[uid]["current"])
    target["pre_rem"] = pre

    # 5️⃣ Agar tahrirlash bo'lsa
    if "edit_target" in users[uid]:
        await reschedule_task(uid, target, context)
        return await tahrir_item_display(update, context)

    # 6️⃣ Yangi eslatma — yakunlash
    users[uid]["reminders"].append(target)
    await reschedule_task(uid, target, context)

    # 🔥 MUVAFFAQIYAT
    await send(
        update,
        get_s(uid, "success"),
        ReplyKeyboardMarkup([[get_s(uid, "btn_back")]], resize_keyboard=True)
    )

    return await menu_display(update, context)
# ===== EDIT & LIST =====
async def tahrir_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    btn_personal = get_s(uid, "btn_personal")
    btn_group = get_s(uid, "btn_group")
    btn_channel = get_s(uid, "btn_channel")
    btn_back = get_s(uid, "btn_back")

    # 1. 🔙 ORQAGA BOSILSA
    if text == btn_back:
        users[uid].pop("list_bolm", None)
        users[uid].pop("target_map", None)
        return await menu_display(update, context)

    # 2. AGAR GURUH/KANAL NOMI TANLANGAN BO'LSA (target_map ichidan qidiramiz)
    if "target_map" in users[uid] and text in users[uid]["target_map"]:
        selected_link = users[uid]["target_map"][text]
        # Shu tanlangan manzilga tegishli barcha eslatmalarni filtrlaymiz
        items = [r for r in users[uid]["reminders"] if str(r.get("link")) == str(selected_link)]
        
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        # Eslatmalar ro'yxatini chiqarish
        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        
        await update.message.reply_text(
            f"📝 {text} — eslatmalari:" if users[uid]["lang"] == "UZ" else f"📝 {text} — заметки:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # 3. SHAXSIY BO'LIM TANLANSA
    if text == btn_personal:
        items = [r for r in users[uid]["reminders"] if r["bolm"] == btn_personal]
        if not items:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb = [[f"📌 {r['text'][:30]}"] for r in items]
        kb.append([btn_back])
        await update.message.reply_text(
            "✏️ Shaxsiy eslatmalar:" if users[uid]["lang"] == "UZ" else "✏️ Личные заметки:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return EXIT_EDIT

    # 4. GURUH YOKI KANAL TUGMASI BOSILSA (Guruhlar ro'yxatini shakllantirish)
    if text in [btn_group, btn_channel]:
        users[uid]["list_bolm"] = text
        users[uid]["target_map"] = {}
        kb = []
        seen = set()

        for r in users[uid]["reminders"]:
            if r["bolm"] == text:
                link = str(r.get("link"))
                if link not in seen:
                    seen.add(link)
                    try:
                        # Guruh/Kanal nomini Telegramdan olamiz
                        chat = await context.bot.get_chat(link)
                        name = chat.title or chat.username or link
                    except:
                        name = link
                    
                    kb.append([name])
                    users[uid]["target_map"][name] = link

        if not kb:
            await update.message.reply_text(get_s(uid, "no_rem"))
            return TAHRIR

        kb.append([btn_back])
        await update.message.reply_text(
            "📂 Kerakli manzilni tanlang:" if users[uid]["lang"] == "UZ" else "📂 Выберите адрес:",
            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
        )
        return TAHRIR # Shunda foydalanuvchi guruh nomini bossa, funksiya qayta ishlaydi va 2-punktga tushadi

    # 5. AGAR NOTO'G'RI MATN KIRITILSA (Boshlang'ich bo'lim tanlash)
    kb = [[btn_personal, btn_group, btn_channel], [btn_back]]
    msg = "📋 Bo'limni tanlang:" if users[uid]["lang"] == "UZ" else "📋 Выберите раздел:"
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return TAHRIR

async def tahrir_item_display(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display reminder details with edit options"""
    uid = update.effective_user.id
    r = users[uid]["edit_target"]
    kb = [
        [get_s(uid, "btn_edit_text"), get_s(uid, "btn_edit_time")],
        [get_s(uid, "btn_edit_rep"), get_s(uid, "btn_edit_pre")],
        [get_s(uid, "btn_toggle"), get_s(uid, "btn_del")],
        [get_s(uid, "btn_back")]
    ]
    await send(update, format_reminder_text(uid, r), ReplyKeyboardMarkup(kb, resize_keyboard=True))
    return EXIT_EDIT


async def exit_edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder editing options"""
    uid = update.effective_user.id
    text = update.message.text

    # 🔙 Back button
    if text == get_s(uid, "btn_back"):
        return await go_back_to_menu(update, context)

    # Select reminder by text if not already selected
    if "edit_target" not in users[uid]:
        for r in users[uid]["reminders"]:
            if r["text"][:30] in text:
                users[uid]["edit_target"] = r
                return await tahrir_item_display(update, context)

    r = users[uid].get("edit_target")
    if not r:
        return MENU

    # Edit options
    if text == get_s(uid, "btn_edit_text"):
        await send(update, get_s(uid, "ask_text"), ReplyKeyboardRemove())
        return MATN

    elif text == get_s(uid, "btn_edit_time"):
        await send(update, get_s(uid, "ask_time"), ReplyKeyboardRemove())
        return VAQT

    elif text == get_s(uid, "btn_edit_rep"):
        await send(update, get_s(uid, "ask_rep"), 
                   ReplyKeyboardMarkup(get_rep_kb(uid), resize_keyboard=True))
        return TAKROR

    elif text == get_s(uid, "btn_edit_pre"):
        # ✅ await chiqarish (get_pre_kb oddiy funksiya)
        await send(update, get_s(uid, "ask_pre"), 
                   ReplyKeyboardMarkup(get_pre_kb(uid), resize_keyboard=True))
        return OLDINDAN

    # Toggle active status
    elif text == get_s(uid, "btn_toggle"):
        r["is_active"] = not r["is_active"]
        await reschedule_task(uid, r, context)
        return await tahrir_item_display(update, context)

    # Delete reminder
    elif text == get_s(uid, "btn_del"):
        users[uid]["reminders"] = [
            x for x in users[uid]["reminders"]
            if x["id"] != r["id"]
        ]
        if r["id"] in tasks.get(uid, {}):
            tasks[uid][r["id"]].cancel()
        users[uid].pop("edit_target", None)
        return await menu_display(update, context)

    return EXIT_EDIT
# ...existing code...
def back_filter():
    return filters.Regex(r"^⬅️")

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("change_lang", change_lang),
            CommandHandler("set_time_zone", set_time_zone),
        ],
        states={
            TIL: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, til_handler),
            ],
            MINTQA: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, mintqa_handler),
            ],
            MENU: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler),
            ],
            YORDAM: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, yordam_handler),
            ],
            BOLM: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, bolm_handler),
            ],
            LINK: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, link_handler),
            ],
            MATN: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, matn_handler),
            ],
            VAQT: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, vaqt_handler),
            ],
            TAKROR: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, takror_handler),
            ],
            OLDINDAN: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, oldindan_handler),
            ],
           TAHRIR: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tahrir_list),
            ],
           EXIT_EDIT: [
                MessageHandler(back_filter(), go_back_to_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, exit_edit_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True
    )
    app.add_handler(conv)

    print("Bot muvaffaqiyatli ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()  