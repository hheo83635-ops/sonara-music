# 🎵 SONARA MUSIC BOT — Setup Guide

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get your Bot Token
1. Open Telegram → find **@BotFather**
2. Send `/newbot`
3. Follow the steps, copy the token
4. In `sonara_bot.py`, replace `"YOUR_BOT_TOKEN_HERE"` with your token

### 3. Run the bot
```bash
python sonara_bot.py
```

---

## How it Works

| Button | Action |
|---|---|
| 📂 OPEN MENU | Opens the main menu |
| 🎵 Choose Music | Search by artist / song title |
| 🆘 HELP | Opens t.me/techsonaramusic |
| 🎶 SONARA MUSIC | Opens t.me/sonarabot_music |
| 🇷🇺 Русский / 🇬🇧 English | Toggles language |

## Search Sources
- **iTunes Search API** — free, no key needed, returns up to 5 real tracks
- **SoundCloud** — direct search link
- **Spotify** — direct search link

## Upgrade to Real API Search (optional)
To get real SoundCloud track listings, register a free app at:
https://developers.soundcloud.com
Then replace `YOUR_SOUNDCLOUD_CLIENT_ID` in the code.

---

## File Structure
```
sonara_bot.py       ← Main bot code
requirements.txt    ← Python dependencies
README.md           ← This file
```

## Keep the bot online 24/7
Deploy to a free server:
- **Railway.app** — free tier, paste code, done
- **Render.com** — free web service
- **PythonAnywhere** — free Python hosting
