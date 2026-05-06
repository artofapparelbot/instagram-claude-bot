CLAUDE_API_KEY = "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"
INSTAGRAM_TOKEN = "IGAATvr1XptdhBZAFlrdjJPUHdQZAm42RGVuNDBMMkhFOG5qM1FBU0VReU1xTDN0ZAVdwdkxybXRmZAE8wZA0tpVzl2el8zT0daOTZATakhLRWtPSEhYbXdrSUstelI3bWZAISjlwMXJFeGpJdDI0cDFCVW51X2d1NUtLblA5S0Rub2dWSQZDZD"
INSTAGRAM_ACCOUNT_ID = "17841479957038966"
VERIFY_TOKEN = "myshopbot123"

BUSINESS_INFO = """
You are a friendly customer service assistant for Art of Apparel Co, a luxury streetwear brand based in Hyderabad.

About us: We sell premium quality custom printed apparel including t-shirts, hoodies, and accessories. We offer bulk printing for businesses and retail for individuals.

Working hours: Monday to Saturday, 10am to 7pm IST
Location: Hyderabad, India

Rules:
- Always reply in the same language the customer uses
- Be friendly, warm and professional
- If asked about pricing, say prices depend on quantity and design and ask them to share requirements
- If you cannot answer something, say: I will get back to you shortly with more details
- Never make up information
"""

import os
import time
import threading
import requests
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
replied_messages = set()

def get_claude_reply(customer_message):
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=300,
            system=BUSINESS_INFO,
            messages=[{"role": "user", "content": customer_message}]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Claude error: {e}")
        return "Thank you for your message! We will get back to you shortly."

def send_instagram_message(recipient_id, message_text):
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text},
            "access_token": INSTAGRAM_TOKEN
        }
        r = requests.post(url, json=payload)
        print(f"Sent reply: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Send error: {e}")

def check_new_messages():
    while True:
        try:
            url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_ACCOUNT_ID}/conversations"
            params = {
                "fields": "messages{message,from,created_time}",
                "access_token": INSTAGRAM_TOKEN
            }
            r = requests.get(url, params=params)
            data = r.json()
            print(f"Checking messages: {r.status_code}")

            if "data" in data:
                for conv in data["data"]:
                    if "messages" in conv and "data" in conv["messages"]:
                        messages = conv["messages"]["data"]
                        if messages:
                            latest = messages[0]
                            msg_id = latest.get("id")
                            msg_text = latest.get("message", "")
                            sender_id = latest.get("from", {}).get("id")

                            if (msg_id not in replied_messages and
                                sender_id and
                                sender_id != INSTAGRAM_ACCOUNT_ID and
                                msg_text):
                                print(f"New message from {sender_id}: {msg_text}")
                                reply = get_claude_reply(msg_text)
                                send_instagram_message(sender_id, reply)
                                replied_messages.add(msg_id)
                                print(f"Replied: {reply}")

        except Exception as e:
            print(f"Check error: {e}")

        time.sleep(30)

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def handle_message():
    data = request.json
    try:
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                sender_id = event["sender"]["id"]
                if "message" in event and "text" in event["message"]:
                    customer_text = event["message"]["text"]
                    msg_id = event["message"].get("mid", "")
                    if msg_id not in replied_messages:
                        print(f"Webhook received: {customer_text}")
                        ai_reply = get_claude_reply(customer_text)
                        send_instagram_message(sender_id, ai_reply)
                        replied_messages.add(msg_id)
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"status": "ok"})

@app.route("/")
def home():
    return "Art of Apparel Bot is running!"

threading.Thread(target=check_new_messages, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
