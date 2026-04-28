import os
import requests
from datetime import datetime

# ─── CONFIG ───────────────────────────────────────────────
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_TOKEN = os.environ["BRAINBOT_TELEGRAM_TOKEN"]
CHAT_ID        = os.environ["BRAINBOT_CHAT_ID"]
GEMINI_URL     = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
# ──────────────────────────────────────────────────────────


def ask_gemini(prompt):
    """Send a prompt to Gemini and get a response."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(GEMINI_URL, json=payload, timeout=30)
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Gemini error: {str(e)}"


def send_telegram(text, chat_id):
    """Send a message via Telegram."""
    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Sent to {chat_id}")
        else:
            print(f"❌ Telegram error: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Send error: {e}")


def handle_message(message):
    """Handle an incoming Telegram message."""
    chat_id = str(message["chat"]["id"])
    text    = message.get("text", "").strip()

    if not text:
        return

    print(f"📩 From {chat_id}: {text}")

    # /start command
    if text == "/start":
        reply = (
            "👋 *Welcome to MyBrainBot!*\n\n"
            "I'm your personal AI assistant for:\n"
            "🤖 AI & Prompt Engineering\n"
            "📈 Marketing & Social Media\n"
            "💼 Business & Sales\n"
            "💰 Finance & Wealth\n\n"
            "*Just ask me anything!*\n\n"
            "Examples:\n"
            "• What is the best prompting technique for marketing?\n"
            "• How do I grow my Instagram using AI?\n"
            "• Give me 5 business ideas using AI tools\n\n"
            "I'm ready! 🚀"
        )

    # /summary command
    elif text == "/summary":
        today = datetime.now().strftime("%B %d, %Y")
        prompt = f"""You are MyBrainBot, a personal AI knowledge assistant.
Today is {today}.

Generate a powerful daily briefing for Telegram covering:
- Latest AI prompting techniques and news
- Marketing and social media strategies
- Business and entrepreneurship insights
- Finance and wealth building tips

Format EXACTLY like this:

🧠 *MyBrainBot Daily — {today}*
━━━━━━━━━━━━━━━━━━━━

📌 *TODAY'S FOCUS*
[Most important insight of the day — 2-3 sentences]

💡 *KEY INSIGHTS*
• [AI/Prompting insight]
• [Marketing insight]
• [Business insight]

🎯 *ACTION OF THE DAY*
[One concrete action to take today]

🔥 *DEEP DIVE*
[Pick one topic and give a 3-4 sentence insight]

━━━━━━━━━━━━━━━━━━━━
🔁 Delivered daily by MyBrainBot"""
        send_telegram("⏳ Generating your daily briefing...", chat_id)
        reply = ask_gemini(prompt)

    # Regular question
    else:
        prompt = f"""You are MyBrainBot, a personal AI assistant specializing in:
- AI & Prompt Engineering
- Marketing & Social Media Strategy  
- Business, Sales & Entrepreneurship
- Finance & Wealth Building

Answer this question clearly and practically for Telegram.
Keep it under 300 words. Use bullet points where helpful.
Be direct and actionable.

Question: {text}"""
        send_telegram("🤔 Thinking...", chat_id)
        reply = ask_gemini(prompt)

    send_telegram(reply, chat_id)


def get_updates(offset=None):
    """Get new messages from Telegram."""
    url    = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json().get("result", [])
    except Exception as e:
        print(f"⚠️ getUpdates error: {e}")
        return []


def delete_webhook():
    """Delete any existing webhook to enable polling."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook"
    requests.get(url, params={"drop_pending_updates": True})
    print("✅ Webhook deleted — polling mode active")


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "poll"

    # Daily summary mode
    if mode == "daily":
        print("📅 Sending daily summary...")
        today  = datetime.now().strftime("%B %d, %Y")
        prompt = f"""You are MyBrainBot. Today is {today}.
Generate a sharp daily briefing covering AI prompting, marketing, business and finance.

Format:
🧠 *MyBrainBot Daily — {today}*
━━━━━━━━━━━━━━━━━━━━

📌 *TODAY'S FOCUS*
[Key insight — 2-3 sentences]

💡 *KEY INSIGHTS*
• [AI insight]
• [Marketing insight]  
• [Business insight]

🎯 *ACTION OF THE DAY*
[One action to take today]

🔥 *DEEP DIVE*
[3-4 sentence insight on trending topic]

━━━━━━━━━━━━━━━━━━━━
🔁 Delivered daily by MyBrainBot"""
        summary = ask_gemini(prompt)
        send_telegram(summary, CHAT_ID)
        return

    # Polling mode
    print("🤖 MyBrainBot is running and listening...")
    delete_webhook()
    offset = None

    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update:
                try:
                    handle_message(update["message"])
                except Exception as e:
                    print(f"⚠️ Handle error: {e}")


if __name__ == "__main__":
    main()
