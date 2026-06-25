from flask import Flask, request
import requests
import pyttsx3

app = Flask(__name__)

# 1. Put your Meta Cloud API details here
WHATSAPP_TOKEN = "YOUR_ACCESS_TOKEN" # from Meta Developers
PHONE_NUMBER_ID = "YOUR_PHONE_NUMBER_ID" # from Meta

engine = pyttsx3.init()

# 2. Your kiosk products + prices
CATALOG = {
    "rice": {"Biryani": 180, "Carveries": 170, "Pishori": 200},
    "unga": {"Unga": 180, "Unga Soko": 175, "Taha Premium": 195},
    "sugar": {"1kg": 160, "2kg": 310},
    "salt": {"500g": 40, "1kg": 75}
}

TILL_NUMBER = "123456" # Replace with your M-Pesa till
BUSINESS_NAME = "Mwalimu Enterprises"

# Simple memory for each customer
user_state = {}

def send_whatsapp(to, message):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "text": {"body": message}}
    requests.post(url, headers=headers, json=data)
    engine.say(message)
    engine.runAndWait()

def handle_message(phone, msg):
    msg = msg.lower().strip()
    state = user_state.get(phone, "start")

    if state == "start" or msg in ["hi", "hello"]:
        user_state[phone] = "menu"
        return f"Welcome to {BUSINESS_NAME}! 🙏 How may I help you?\n\nType a product name for prices:\nRice, Unga, Sugar, Salt\nType 'list' for full catalog"

    if state == "menu":
        for product, items in CATALOG.items():
            if product in msg:
                user_state[phone] = f"pick_{product}"
                options = "\n".join([f"{k}: Ksh {v}" for k,v in items.items()])
                return f"{product.title()} prices:\n{options}\n\nReply with the type you want, e.g. 'Biryani'"

        if "list" in msg:
            full = ""
            for p, items in CATALOG.items():
                full += f"\n{p.title()}:\n" + "\n".join([f" {k}: Ksh {v}" for k,v in items.items()])
            return f"Full catalog:{full}\n\nWhich one do you want?"

        return "Sorry, I didn’t get that. Try: Rice, Unga, Sugar, or Salt"

    if state.startswith("pick_"):
        product = state.split("_")[1]
        for item, price in CATALOG[product].items():
            if item.lower() in msg:
                user_state[phone] = f"qty_{product}_{item}_{price}"
                return f"{item} rice is Ksh {price} per kg. How many kgs do you want?"
        return f"Please pick one: {', '.join(CATALOG[product].keys())}"

    if state.startswith("qty_"):
        _, product, item, price = state.split("_")
        try:
            qty = float(msg.replace("kg", "").strip())
            total = int(float(price) * qty)
            user_state[phone] = f"pay_{total}"
            return f"Total for {qty}kg {item}: Ksh {total}\n\nPay via M-Pesa Till {TILL_NUMBER}\nThen send me the MPESA code here"
        except:
            return "Please reply with number only, e.g. 2 or 2kg"

    if state.startswith("pay_"):
        total = state.split("_")[1]
        user_state[phone] = "start"
        return f"Payment code received! ✅\n\nThank you for buying from {BUSINESS_NAME}. Your order of Ksh {total} is confirmed. Come again soon! 🙏"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Meta verification
        if request.args.get("hub.verify_token") == "FridaySecretToken":
            return request.args.get("hub.challenge")
        return "Verification failed"

    # Incoming WhatsApp message
    data = request.get_json()
    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = msg["from"]
        text = msg["text"]["body"]
        reply = handle_message(phone, text)
        send_whatsapp(phone, reply)
    except:
        pass
    return "ok"

if __name__ == "__main__":
    app.run(port=5000)