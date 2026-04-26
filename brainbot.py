import os
import json
import requests
import feedparser
from groq import Groq
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN = os.environ["BRAINBOT_TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["BRAINBOT_CHAT_ID"]
SOURCES_FILE   = "sources.json"
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
# ──────────────────────────────────────────────────────────


# ─── SOURCES MANAGEMENT ───────────────────────────────────

def load_sources():
    """Load saved sources from file."""
    if os.path.exists(SOURCES_FILE):
        with open(SOURCES_FILE, "r") as f:
            return json.load(f)
    return {"youtube": [], "notes": []}


def save_sources(sources):
    """Save sources to file."""
    with open(SOURCES_FILE, "w") as f:
        json.dump(sources, f, indent=2)


def add_youtube(url):
    """Add a YouTube link to sources."""
    sources = load_sources()
    if url not in sources["youtube"]:
        sources["youtube"].append(url)
        save_sources(sources)
        return True
    return False


def add_note(text):
    """Add a text note to sources."""
    sources = load_sources()
    sources["notes"].append({
        "text": text,
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_sources(sources)


# ─── GEMINI API ───────────────────────────────────────────

def ask_gemini(prompt):
    """Send a prompt to Gemini and get a response."""
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    r = requests.post(GEMINI_URL, json=payload)
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return "⚠️ Gemini could not generate a response. Please try again."


# ─── DAILY SUMMARY ────────────────────────────────────────

def generate_daily_summary():
    """Generate a daily summary from all saved sources."""
    sources = load_sources()
    today   = datetime.now().strftime("%B %d, %Y")

    youtube_block = ""
    for i, url in enumerate(sources["youtube"][-10:], 1):
        youtube_block += f"{i}. {url}\n"

    notes_block = ""
    for i, note in enumerate(sources["notes"][-10:], 1):
        notes_block += f"{i}. [{note['date']}] {note['text']}\n"

    if not youtube_block and not notes_block:
        return (
            f"🧠 *MyBrainBot Daily — {today}*\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "📭 No sources added yet!\n\n"
            "Send me:\n"
            "• A YouTube link to add it\n"
            "• /note followed by any text to save a note\n"
            "• Any question and I'll answer it\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔁 Delivered daily by MyBrainBot"
        )

    prompt = f"""You are MyBrainBot, a personal AI knowledge assistant.
Today is {today}.

The user has shared these YouTube video links about AI, marketing, business, finance and social media:
{youtube_block if youtube_block else "None yet."}

And these personal notes:
{notes_block if notes_block else "None yet."}

Based on these sources, generate a powerful daily briefing for Telegram with this EXACT format:

🧠 *MyBrainBot Daily — {today}*
━━━━━━━━━━━━━━━━━━━━

📌 *TODAY'S FOCUS*
[Pick the most relevant topic from the sources and write 2-3 sentences about why it matters today]

💡 *KEY INSIGHTS*
• [Insight 1 from the sources]
• [Insight 2 from the sources]
• [Insight 3 from the sources]

🎯 *ACTION OF THE DAY*
[One concrete action the user can take today based on their sources]

📚 *FROM YOUR NOTES*
[Reference any saved notes and connect them to today's theme]

🔥 *TOPIC DEEP DIVE*
[Pick one topic from AI prompting, marketing, or business and give a 3-4 sentence insight]

━━━━━━━━━━━━━━━━━━━━
🔁 Delivered daily by MyBrainBot"""

    return ask_gemini(prompt)


# ─── ANSWER QUESTIONS ─────────────────────────────────────

def answer_question(question):
    """Answer a user question using Gemini with sources as context."""
    sources  = load_sources()

    youtube_block = "\n".join(sources["youtube"][-10:]) if sources["youtube"] else "None"
    notes_block   = "\n".join([n["text"] for n in sources["notes"][-10:]]) if sources["notes"] else "None"

    prompt = f"""You are MyBrainBot, a personal AI knowledge assistant specializing in:
- AI & Prompt Engineering
- Marketing & Social Media Strategy
- Business, Sales & Finance
- Content Creation & YouTube

The user has these saved YouTube sources:
{youtube_block}

And these personal notes:
{notes_block}

Now answer this question clearly and concisely for Telegram:
Question: {question}

Keep your answer practical, actionable, and under 300 words.
Use bullet points where helpful."""

    return ask_gemini(prompt)


# ─── TELEGRAM ─────────────────────────────────────────────

def send_telegram(text, chat_id=None):
    """Send a message via Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id or CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        print("✅ Message sent!")
    else:
        print(f"❌ Error: {r.status_code} — {r.text}")


def get_updates(offset=None):
    """Get new messages from Telegram."""
    url    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    r = requests.get(url, params=params)
    return r.json().get("result", [])


def set_webhook_off():
    """Make sure polling mode works by deleting any webhook."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
    requests.get(url)


# ─── PROCESS INCOMING MESSAGES ────────────────────────────

def handle_message(message):
    """Handle an incoming Telegram message."""
    chat_id = message["chat"]["id"]
    text    = message.get("text", "").strip()

    if not text:
        return

    print(f"📩 Message received: {text}")

    # Command: /start
    if text == "/start":
        reply = (
            "👋 *Welcome to MyBrainBot!*\n\n"
            "I'm your personal AI knowledge assistant.\n\n"
            "*What I can do:*\n"
            "• Send you daily summaries every morning\n"
            "• Answer your questions on AI, marketing, business & finance\n"
            "• Remember your YouTube links and notes\n\n"
            "*Commands:*\n"
            "• Send any *YouTube link* → I'll save it as a source\n"
            "• /note [text] → Save a personal note\n"
            "• /summary → Get today's summary now\n"
            "• /sources → See all your saved sources\n"
            "• /clear → Clear all sources\n"
            "• Any *question* → I'll answer it!\n\n"
            "Let's go! 🚀"
        )

    # Command: /summary
    elif text == "/summary":
        send_telegram("⏳ Generating your summary...", chat_id)
        reply = generate_daily_summary()

    # Command: /sources
    elif text == "/sources":
        sources       = load_sources()
        youtube_list  = "\n".join([f"• {url}" for url in sources["youtube"]]) or "None yet"
        notes_list    = "\n".join([f"• {n['text']}" for n in sources["notes"]]) or "None yet"
        reply = (
            f"📚 *Your Saved Sources*\n\n"
            f"🎥 *YouTube Links:*\n{youtube_list}\n\n"
            f"📝 *Notes:*\n{notes_list}"
        )

    # Command: /clear
    elif text == "/clear":
        save_sources({"youtube": [], "notes": []})
        reply = "🗑️ All sources cleared successfully!"

    # Command: /note
    elif text.startswith("/note "):
        note = text[6:].strip()
        if note:
            add_note(note)
            reply = f"📝 Note saved: _{note}_"
        else:
            reply = "Please add text after /note. Example: /note AI agents are the future"

    # YouTube link detected
    elif "youtube.com" in text or "youtu.be" in text:
        added = add_youtube(text)
        if added:
            reply = (
                f"🎥 YouTube link saved!\n\n"
                f"I'll include it in your daily summaries.\n"
                f"You can also ask me questions about this topic anytime."
            )
        else:
            reply = "This YouTube link is already in your sources! ✅"

    # Regular question — answer with Gemini
    else:
        send_telegram("🤔 Let me think...", chat_id)
        reply = answer_question(text)

    send_telegram(reply, chat_id)


# ─── MAIN ─────────────────────────────────────────────────

def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "poll"

    # Daily summary mode (called by GitHub Actions scheduler)
    if mode == "daily":
        print("📅 Running daily summary...")
        summary = generate_daily_summary()
        send_telegram(summary)
        return

    # Polling mode (runs continuously to receive messages)
    print("🤖 MyBrainBot is running and listening...")
    set_webhook_off()
    offset = None

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                handle_message(update["message"])


if __name__ == "__main__":
    main()
