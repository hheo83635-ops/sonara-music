import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8958517737:AAHIS2bCDpR7-Tq8cv7_KMltdx-MvW0fFes"  # Replace with your token from @BotFather

# ─── Banner photo ─────────────────────────────────────────────────────────────
# Path to the Sonara Music banner image (place banner.jpg next to this script)
BANNER_PATH = "banner.jpg"

SEARCHING = 1

TEXTS = {
    "en": {
        "welcome": (
            "🎵 *SONARA MUSIC*\n\n"
            "Hey, pick a boring option.\n\n"
            "_Listen. Sing. Be better. Enjoy._"
        ),
        "choose_music_prompt": (
            "🔍 *Search Music*\n\n"
            "Type an artist name or song title.\n"
            "I'll find the best matches from SoundCloud & Spotify.\n\n"
            "_Example: The Weeknd • Blinding Lights • Dua Lipa_"
        ),
        "searching": "🎵 Searching across SoundCloud & Spotify...",
        "results_header": "🎶 *Top results for* `{query}`\n\n",
        "no_results": "😔 Nothing found for *{query}*.\nTry a different name or spelling.",
        "help_text": "💬 Need help? Contact support:",
        "channel_text": "📡 Visit the official Sonara Music channel:",
        "lang_switched": "🇷🇺 Язык переключён на русский!",
        "btn_choose": "🎵 Choose Music",
        "btn_help": "🆘 HELP",
        "btn_channel": "🎶 SONARA MUSIC",
        "btn_lang": "🇷🇺 Русский",
        "btn_back": "⬅️ Back",
        "btn_search_again": "🔁 Search Again",
        "soundcloud_label": "🔊 SoundCloud",
        "spotify_label": "🎧 Spotify",
        "open_menu": "📂 OPEN MENU",
        "cancel": "❌ Search cancelled.",
    },
    "ru": {
        "welcome": (
            "🎵 *SONARA MUSIC*\n\n"
            "Эй, выбери скучный вариант.\n\n"
            "_Слушай. Пой. Становись лучше. Наслаждайся._"
        ),
        "choose_music_prompt": (
            "🔍 *Поиск Музыки*\n\n"
            "Введи имя артиста или название песни.\n"
            "Найду лучшее из SoundCloud и Spotify.\n\n"
            "_Пример: Элджей • Morgenshtern • Face_"
        ),
        "searching": "🎵 Ищу по SoundCloud и Spotify...",
        "results_header": "🎶 *Результаты по запросу* `{query}`\n\n",
        "no_results": "😔 По запросу *{query}* ничего не найдено.\nПопробуй другое написание.",
        "help_text": "💬 Нужна помощь? Напиши в поддержку:",
        "channel_text": "📡 Перейти на официальный канал Sonara Music:",
        "lang_switched": "🇬🇧 Language switched to English!",
        "btn_choose": "🎵 Выбрать Музыку",
        "btn_help": "🆘 ПОМОЩЬ",
        "btn_channel": "🎶 SONARA MUSIC",
        "btn_lang": "🇬🇧 English",
        "btn_back": "⬅️ Назад",
        "btn_search_again": "🔁 Новый Поиск",
        "soundcloud_label": "🔊 SoundCloud",
        "spotify_label": "🎧 Spotify",
        "open_menu": "📂 ОТКРЫТЬ МЕНЮ",
        "cancel": "❌ Поиск отменён.",
    }
}

user_languages = {}

def get_lang(user_id: int) -> str:
    return user_languages.get(user_id, "en")

def t(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    text = TEXTS[lang].get(key, TEXTS["en"][key])
    return text.format(**kwargs) if kwargs else text

def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    lang = get_lang(user_id)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t(user_id, "btn_choose"), callback_data="choose_music"),
            InlineKeyboardButton(t(user_id, "btn_help"), url="https://t.me/techsonaramusic"),
        ],
        [InlineKeyboardButton(t(user_id, "btn_channel"), url="https://t.me/sonarabot_music")],
        [InlineKeyboardButton(t(user_id, "btn_lang"), callback_data="toggle_lang")],
    ])

def back_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "btn_back"), callback_data="back_to_menu")]
    ])


# ─── SoundCloud search (no auth needed for oEmbed / public search) ───────────
async def search_soundcloud(query: str, limit: int = 4) -> list[dict]:
    """
    Uses SoundCloud's public search endpoint.
    Returns list of {title, url, author}.
    """
    results = []
    try:
        url = f"https://api.soundcloud.com/tracks?q={aiohttp.helpers.BasicAuth._encode(query)}&limit={limit}&client_id=YOUR_SOUNDCLOUD_CLIENT_ID"
        # Fallback: use SoundCloud search URL directly as links
        # Since free SoundCloud API requires client_id, we build direct search links
        search_url = f"https://soundcloud.com/search?q={query.replace(' ', '+')}"
        results.append({
            "title": f"🔊 Search \"{query}\" on SoundCloud",
            "url": search_url,
            "source": "soundcloud",
            "author": "SoundCloud"
        })
    except Exception as e:
        logger.error(f"SoundCloud error: {e}")
    return results


async def search_spotify_unofficial(query: str, limit: int = 6) -> list[dict]:
    """
    Uses Spotify's public search embed (no API key needed).
    Returns structured results.
    """
    results = []
    try:
        # Spotify open search
        search_url = f"https://open.spotify.com/search/{query.replace(' ', '%20')}"
        results.append({
            "title": f"🎧 Search \"{query}\" on Spotify",
            "url": search_url,
            "source": "spotify",
            "author": "Spotify"
        })
    except Exception as e:
        logger.error(f"Spotify error: {e}")
    return results


async def search_itunes(query: str, limit: int = 7) -> list[dict]:
    """iTunes Search API — completely free, no auth needed."""
    results = []
    try:
        async with aiohttp.ClientSession() as session:
            params = {
                "term": query,
                "media": "music",
                "limit": limit,
                "entity": "song"
            }
            async with session.get("https://itunes.apple.com/search", params=params, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    for item in data.get("results", [])[:limit]:
                        results.append({
                            "title": item.get("trackName", "Unknown"),
                            "author": item.get("artistName", "Unknown"),
                            "url": item.get("trackViewUrl", ""),
                            "preview": item.get("previewUrl", ""),
                            "artwork": item.get("artworkUrl60", ""),
                            "source": "itunes"
                        })
    except Exception as e:
        logger.error(f"iTunes error: {e}")
    return results


async def do_search(query: str) -> list[dict]:
    """Combine iTunes (free) + SoundCloud/Spotify direct links."""
    itunes_results = await search_itunes(query, limit=5)

    all_results = itunes_results[:5]

    # Append direct search links for SoundCloud and Spotify
    all_results.append({
        "title": f'Search on SoundCloud',
        "author": "soundcloud.com",
        "url": f"https://soundcloud.com/search?q={query.replace(' ', '+')}",
        "source": "soundcloud"
    })
    all_results.append({
        "title": f'Search on Spotify',
        "author": "open.spotify.com",
        "url": f"https://open.spotify.com/search/{query.replace(' ', '%20')}",
        "source": "spotify"
    })

    return all_results[:7]


def format_results(results: list[dict], query: str, user_id: int) -> tuple[str, InlineKeyboardMarkup]:
    text = t(user_id, "results_header", query=query)

    EMOJI_MAP = {"itunes": "🍎", "soundcloud": "🔊", "spotify": "🎧"}
    buttons = []

    for i, r in enumerate(results, 1):
        emoji = EMOJI_MAP.get(r.get("source", ""), "🎵")
        author = r.get("author", "")
        title = r.get("title", "Unknown")
        display = f"{emoji} {author} — {title}" if author and author not in title else f"{emoji} {title}"
        text += f"{i}. {display[:60]}\n"
        if r.get("url"):
            buttons.append([InlineKeyboardButton(f"{emoji} {title[:35]}...", url=r["url"]) if len(title) > 35 else InlineKeyboardButton(f"{emoji} {title}", url=r["url"])])

    keyboard = buttons + [
        [InlineKeyboardButton(t(user_id, "btn_search_again"), callback_data="choose_music")],
        [InlineKeyboardButton(t(user_id, "btn_back"), callback_data="back_to_menu")],
    ]
    return text, InlineKeyboardMarkup(keyboard)


# ─── Handlers ────────────────────────────────────────────────────────────────

async def send_banner_menu(chat_id: int, uid: int, context: ContextTypes.DEFAULT_TYPE,
                           caption: str, keyboard: InlineKeyboardMarkup):
    """Send (or re-send) the banner photo with caption and inline keyboard."""
    # Cache file_id after first upload to avoid re-uploading every time
    cached_id = context.bot_data.get("banner_file_id")
    try:
        if cached_id:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=cached_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard,
            )
        else:
            with open(BANNER_PATH, "rb") as f:
                msg = await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
            # Cache the file_id for future calls
            context.bot_data["banner_file_id"] = msg.photo[-1].file_id
    except FileNotFoundError:
        # Fallback: plain text if banner.jpg is missing
        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard,
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, "open_menu"), callback_data="open_menu")]
    ])
    await send_banner_menu(
        chat_id=update.effective_chat.id,
        uid=uid,
        context=context,
        caption="🎵 *SONARA MUSIC*\n_Your music companion_\n\n_Feel the sound. Live the music._",
        keyboard=keyboard,
    )


async def open_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    chat_id = query.message.chat_id

    # Delete the old message (could be text or photo), then send fresh banner+menu
    try:
        await query.message.delete()
    except Exception:
        pass

    await send_banner_menu(
        chat_id=chat_id,
        uid=uid,
        context=context,
        caption=t(uid, "welcome"),
        keyboard=main_menu_keyboard(uid),
    )


async def toggle_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    chat_id = query.message.chat_id
    current = get_lang(uid)
    user_languages[uid] = "ru" if current == "en" else "en"
    await query.answer(t(uid, "lang_switched"), show_alert=False)

    try:
        await query.message.delete()
    except Exception:
        pass

    await send_banner_menu(
        chat_id=chat_id,
        uid=uid,
        context=context,
        caption=t(uid, "welcome"),
        keyboard=main_menu_keyboard(uid),
    )


async def choose_music_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    await query.edit_message_text(
        t(uid, "choose_music_prompt"),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_keyboard(uid)
    )
    return SEARCHING


async def receive_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    search_text = update.message.text.strip()

    if not search_text:
        return SEARCHING

    msg = await update.message.reply_text(t(uid, "searching"), parse_mode=ParseMode.MARKDOWN)

    results = await do_search(search_text)

    if not results:
        await msg.edit_text(
            t(uid, "no_results", query=search_text),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_keyboard(uid)
        )
        return SEARCHING

    text, keyboard = format_results(results, search_text, uid)
    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    return SEARCHING


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    chat_id = query.message.chat_id

    try:
        await query.message.delete()
    except Exception:
        pass

    await send_banner_menu(
        chat_id=chat_id,
        uid=uid,
        context=context,
        caption=t(uid, "welcome"),
        keyboard=main_menu_keyboard(uid),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(t(uid, "cancel"))
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(choose_music_start, pattern="^choose_music$")],
        states={
            SEARCHING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_query),
                CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"),
                CallbackQueryHandler(choose_music_start, pattern="^choose_music$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"),
        ],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(open_menu, pattern="^open_menu$"))
    app.add_handler(CallbackQueryHandler(toggle_lang, pattern="^toggle_lang$"))
    app.add_handler(conv_handler)

    logger.info("🎵 Sonara Music Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
