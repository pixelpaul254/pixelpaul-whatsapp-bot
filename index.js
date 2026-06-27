const express = require("express");
const app = express();
app.use(express.json());

const prices = {
  "unga": "Unga 2kg is KSh 180",
  "maize flour": "Maize Flour 2kg is KSh 180",
  "sugar": "Sugar 1kg is KSh 160",
  "rice": "Rice 1kg is KSh 120",
  "cooking oil": "Cooking Oil 1L is KSh 280",
  "milk": "Milk 500ml is KSh 60",
  "bread": "Bread is KSh 65",
  "salt": "Salt 500g is KSh 30",
  "tomatoes": "Tomatoes 1kg is KSh 80",
  "onions": "Onions 1kg is KSh 70",
};

app.get("/webhook", (req, res) => {
  const VERIFY_TOKEN = process.env.VERIFY_TOKEN || "pixelpaul2024";
  if (req.query["hub.mode"] === "subscribe" && req.query["hub.verify_token"] === VERIFY_TOKEN) {
    res.status(200).send(req.query["hub.challenge"]);
  } else {
    res.sendStatus(403);
  }
});

app.post("/webhook", async (req, res) => {
  console.log("Webhook received!");
  console.log(JSON.stringify(req.body, null, 2));

  try {
    const message = req.body.entry[0].changes[0].value.messages[0];
    const from = message.from;
    const text = message.text?.body?.toLowerCase().trim();
    let reply = "Sorry, I don't have that price. Try: unga, sugar, rice, cooking oil, milk, bread, salt, tomatoes, onions.";
    for (const [keyword, price] of Object.entries(prices)) {
      if (text && text.includes(keyword)) {
        reply = "✅ " + price;
        break;
      }
    }
    await fetch(`https://graph.facebook.com/v19.0/${process.env.PHONE_NUMBER_ID}/messages`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messaging_product: "whatsapp",
        to: from,
        text: { body: reply },
      }),
    });
    res.sendStatus(200);
  } catch (err) {
    console.error("Error handling webhook:", err);
    res.sendStatus(200);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("Bot running on port " + PORT));
