CLAUDE_API_KEY = "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"        # paste your Claude API key here
INSTAGRAM_TOKEN = "IGAATvr1XptdhBZAGI4YS1YMmhDazgyOHdyUTZAHcWlKMWZAhRGJDNUk4SC05bXQyVnlzX3R3bEdOdXlLZAl9lZA2tDTFI3aUlQVWtVUlRiNGtYdHBTZAFBiRzBfMnNoQlRTQzNVY1lBbjE4M3BDSkJTd3RIa1BiZAGJhUmpLX3ZAKS3IxdwZDZD"    # paste your Access Token here
VERIFY_TOKEN = "myshopbot123"        # leave this exactly as written

BUSINESS_INFO = """
You are a friendly customer service assistant for Art of Apparel Co, a luxury streetwear brand based in Hyderabad.

About us: We sell premium quality custom printed apparel including t-shirts, hoodies, and accessories. We offer bulk printing for businesses and retail for individuals.

Working hours: Monday to Saturday, 10am to 7pm IST
Location: Hyderabad, India
Contact: Message us here or call us directly for urgent queries

Rules:
- Always reply in the same language the customer uses
- Be friendly, warm and professional
- If asked about pricing, say prices depend on quantity and design and ask them to share requirements
- If you cannot answer something, say: I will get back to you shortly with more details
- Never make up information
"""

import os
import requests
from flask import Flask, request, jsonify
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

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
        print(f"Sent message: {r.status_code}")
    except Exception as e:
        print(f"Send error: {e}")

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
                    print(f"Received from {sender_id}: {customer_text}")
                    ai_reply = get_claude_reply(customer_text)
                    send_instagram_message(sender_id, ai_reply)
    except Exception as e:
        print(f"Webhook error: {e}")
    return jsonify({"status": "ok"})

@app.route("/")
def home():
    return "Art of Apparel Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
