"""Rule-Based Interactive Terminal Assistant (Chatbot)

Run with:  python chatbot.py

A customer-support bot for a fictional store ("ShopEase"). It:
- normalizes input (lowercase, trimmed, extra spaces removed),
- recognizes intents with regular expressions and keywords,
- answers several questions in one message (multi-intent),
- remembers context (user's name, last topic, "tell me more"),
- falls back gracefully when it does not understand,
- exits cleanly with 'bye', 'exit' or 'quit'.

Optional: put a file named 'faq.json' next to this script to add or override
intents. Format:
{
  "intents": {
    "warranty": {
      "patterns": ["\\\\bwarranty\\\\b", "\\\\bguarantee\\\\b"],
      "response": "All products come with a 1-year warranty.",
      "details": "Optional longer answer for 'tell me more'."
    }
  }
}
"""

import json
import os
import random
import re

BOT_NAME = "ShopEase Assistant"
STORE_NAME = "ShopEase"
FAQ_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "faq.json")

# Each intent: regex patterns (any match counts), a response, and optional details.
INTENTS = {
    "greeting": {
        "patterns": [r"\b(hi|hello|hey|hola|salam)\b",
                     r"\bassalam[\s-]*o[\s-]*alaikum\b",
                     r"\bgood\s+(morning|afternoon|evening)\b"],
        "response": [f"Hello! Welcome to {STORE_NAME}. How can I help you today?",
                     "Hi there! What can I help you with?"],
    },
    "hours": {
        "patterns": [r"\b(hours?|timings?|schedule)\b", r"\bwhat\s+time\b",
                     r"\bwhen\b.*\b(open|close)\b", r"\b(open|opening|closing|closed)\b",
                     r"\bopen\s+(on|today|now)\b"],
        "response": "We are open Monday to Saturday, 9:00 AM to 8:00 PM. We are closed on Sundays.",
        "details": "Online orders are accepted 24/7, but they are processed during business hours. "
                   "On public holidays we close at 5:00 PM.",
    },
    "location": {
        "patterns": [r"\b(location|located|address|directions?|branch(es)?|visit)\b",
                     r"\bwhere\b.*\b(you|your|store|shop|office|find)\b(?!.*\border\b)",
                     r"\bstore\s+(near|locat)"],
        "response": f"{STORE_NAME} main store: 12 Blue Area, Islamabad. We also have branches in Lahore and Karachi.",
        "details": "Free parking is available at the Islamabad store. The closest landmark is the Jinnah Super Market.",
    },
    "products": {
        "patterns": [r"\b(products?|items?|catalog(ue)?|sell|selling|in\s+stock)\b",
                     r"\b(laptops?|phones?|mobiles?|headphones?|accessories|tablets?|chargers?)\b",
                     r"\bwhat\s+do\s+you\s+(sell|offer)\b"],
        "response": "We sell laptops, smartphones, tablets, headphones and accessories (chargers, cases, cables) "
                    "from brands like HP, Dell, Samsung and Apple.",
        "details": "Ask about prices, warranty or delivery for any product. New arrivals are added every week.",
    },
    "pricing": {
        "patterns": [r"\b(price|prices|pricing|cost|costs|how\s+much|cheap|expensive|discount|offers?|sale|deal)\b"],
        "response": "Prices start from Rs. 1,500 for accessories and Rs. 35,000 for smartphones. "
                    "Laptops start from Rs. 85,000. We run discounts every weekend.",
        "details": "Students get an extra 5% off with a valid student ID. Ask in-store or at checkout.",
    },
    "shipping": {
        "patterns": [r"\b(ship|shipping|deliver|delivery|dispatch|courier|arrive|arrival)\b"],
        "response": "We deliver across Pakistan. Delivery takes 2-4 working days. It is free for orders above Rs. 5,000, "
                    "otherwise the charge is Rs. 250.",
        "details": "Big cities usually receive orders in 1-2 days. You will get a tracking number by SMS.",
    },
    "returns": {
        "patterns": [r"\b(returns?|refunds?|exchange|replace(ment)?|money\s+back|cancel(lation)?)\b"],
        "response": "You can return or exchange any item within 7 days of delivery if it is unused and in its original packaging.",
        "details": "Refunds are issued to your original payment method within 5-7 working days after we receive the item.",
    },
    "payment": {
        "patterns": [r"\b(pay|payment|payments|card|credit|debit|cash|cod|easypaisa|jazzcash|installments?)\b"],
        "response": "We accept cash on delivery, debit/credit cards, bank transfer, Easypaisa and JazzCash.",
        "details": "0% installment plans are available on selected laptops with partner banks.",
    },
    "warranty": {
        "patterns": [r"\b(warranty|guarantee|guaranty|repair)\b"],
        "response": "All new products include a 1-year warranty. Keep your receipt for any warranty claim.",
        "details": "Warranty covers manufacturing defects. It does not cover physical or water damage.",
    },
    "contact": {
        "patterns": [r"\b(contact|phone|call|email|e-mail|whatsapp|support|helpline|human|agent|representative)\b"],
        "response": "You can reach us at 051-1234567, or email support@shopease.example. WhatsApp: 0300-1234567.",
        "details": "Our support team replies to emails within 24 hours.",
    },
    "order_status": {
        "patterns": [r"\b(order|tracking|track|parcel|package)\b"],
        "response": "To check an order, please tell me your order number (for example: order #12345).",
    },
    "thanks": {
        "patterns": [r"\b(thanks?|thank\s+you|thx|shukriya|jazak\s?allah)\b"],
        "response": ["You're welcome! Anything else I can help with?",
                     "Happy to help! Let me know if you need anything else."],
    },
    "help": {
        "patterns": [r"\b(help|menu|options|what\s+can\s+you\s+do)\b"],
        "response": "I can help with: business hours, store location, products, prices, delivery, returns, "
                    "payments, warranty, order tracking and contact details. Just ask!",
    },
}

EXIT_PATTERN = re.compile(r"^\s*(bye|goodbye|good\s*bye|exit|quit|see\s+you|q)\s*[.!]*\s*$", re.I)
NAME_PATTERN = re.compile(r"\b(?:my\s+name\s+is|call\s+me)\s+([a-z][a-z'-]{1,20})\b", re.I)
ORDER_PATTERN = re.compile(r"\b(?:order|ord|tracking)?\s*(?:no\.?|number|id|#)?\s*[#:]?\s*(\d{4,10})\b", re.I)
MORE_PATTERN = re.compile(r"\b(more|details?|elaborate|explain|tell\s+me\s+more)\b", re.I)
YES_PATTERN = re.compile(r"^\s*(yes|yeah|yep|sure|ok(ay)?|please|haan|ji)\s*[.!]*\s*$", re.I)
NO_PATTERN = re.compile(r"^\s*(no|nope|nah|nothing|no\s+thanks|nahi)\s*[.!]*\s*$", re.I)

MAX_INTENTS_PER_REPLY = 3
# Fixed pseudo-statuses for demo order tracking (based on the last digit)
ORDER_STATUSES = ["is being packed", "has been shipped", "is out for delivery",
                  "was delivered", "is waiting for payment confirmation"]


def normalize(text):
    """Lowercase, trim and collapse repeated whitespace."""
    return re.sub(r"\s+", " ", text.strip().lower())


def load_faq_file(intents, path=FAQ_FILE):
    """Merge extra intents from faq.json if the file exists and is valid."""
    if not os.path.exists(path):
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        added = 0
        for name, spec in data.get("intents", {}).items():
            patterns = [re.compile(p, re.I) for p in spec["patterns"]]  # validates regexes
            if not patterns or "response" not in spec:
                raise KeyError(name)
            intents[name] = {"patterns": spec["patterns"], "response": spec["response"],
                             "details": spec.get("details")}
            added += 1
        return added
    except (OSError, ValueError, KeyError, TypeError, re.error, AttributeError) as exc:
        print(f"[Warning] Could not load faq.json ({exc}). Using built-in answers only.")
        return 0


def compile_intents(intents):
    return {name: [re.compile(p, re.I) for p in spec["patterns"]] for name, spec in intents.items()}


def detect_intents(text, compiled):
    """Return intent names sorted by where they appear in the sentence (best score first on ties)."""
    found = []
    for name, patterns in compiled.items():
        positions, score = [], 0
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                score += 1
                positions.append(match.start())
        if score:
            found.append((min(positions), -score, name))
    found.sort()
    return [name for _, _, name in found]


def pick(response):
    return random.choice(response) if isinstance(response, list) else response


class Session:
    """Conversation state: greeting -> assisting -> exit."""

    def __init__(self):
        self.state = "greeting"
        self.user_name = None
        self.last_intent = None
        self.fallbacks = 0
        self.awaiting_order_number = False


def order_reply(order_number):
    status = ORDER_STATUSES[int(order_number[-1]) % len(ORDER_STATUSES)]
    return f"Order #{order_number} {status}. (This is demo data.) Anything else?"


def respond(raw, session, intents, compiled):
    """Return (reply, should_exit)."""
    text = normalize(raw)

    if not text:
        return "I didn't catch that. Could you type your question?", False

    if EXIT_PATTERN.match(text):
        name = f", {session.user_name}" if session.user_name else ""
        return f"Goodbye{name}! Thanks for contacting {STORE_NAME}. Have a great day!", True

    parts = []

    # Remember the user's name
    name_match = NAME_PATTERN.search(raw)
    if name_match:
        session.user_name = name_match.group(1).capitalize()
        parts.append(f"Nice to meet you, {session.user_name}!")

    # Order tracking flow (needs an order number)
    order_match = ORDER_PATTERN.search(text)
    if order_match and (session.awaiting_order_number or re.search(r"\b(order|tracking|track)\b", text)):
        session.awaiting_order_number = False
        session.last_intent = "order_status"
        session.fallbacks = 0
        parts.append(order_reply(order_match.group(1)))
        session.state = "assisting"
        return " ".join(parts), False

    # Short answers to follow-up questions
    if YES_PATTERN.match(text) and session.last_intent:
        details = intents.get(session.last_intent, {}).get("details")
        return (details or "Great! What else would you like to know?"), False
    if NO_PATTERN.match(text):
        return "Okay! If you need anything else, just ask. Type 'bye' to exit.", False

    found = detect_intents(text, compiled)

    # "tell me more" refers to the previous topic
    if MORE_PATTERN.search(text) and session.last_intent and not [i for i in found if i not in ("help",)]:
        details = intents.get(session.last_intent, {}).get("details")
        if details:
            return details, False

    if found:
        session.fallbacks = 0
        session.state = "assisting"
        for name in found[:MAX_INTENTS_PER_REPLY]:
            parts.append(pick(intents[name]["response"]))
        session.last_intent = found[0] if len(found) == 1 else found[-1]
        session.awaiting_order_number = "order_status" in found[:MAX_INTENTS_PER_REPLY]
        reply = "\n".join(parts) if len(parts) > 1 else parts[0]
        if intents.get(session.last_intent, {}).get("details") and len(found) == 1 \
                and session.last_intent != "order_status":
            reply += "\n(Type 'more' for extra details.)"
        return reply, False

    # Name only, e.g. "my name is Ali"
    if name_match:
        return " ".join(parts) + " How can I help you today?", False

    # Fallback for unrecognized input
    session.fallbacks += 1
    if session.fallbacks >= 2:
        return ("I'm still not sure what you mean. I can help with hours, location, products, prices, "
                "delivery, returns, payments, warranty or order tracking. You can also call 051-1234567."), False
    return "Sorry, I didn't understand that. Could you rephrase it? Type 'help' to see what I can do.", False


def main():
    intents = dict(INTENTS)
    extra = load_faq_file(intents)
    compiled = compile_intents(intents)
    session = Session()

    print("=" * 52)
    print(f"  {BOT_NAME}")
    print("  Type your question. Type 'bye', 'exit' or 'quit' to leave.")
    if extra:
        print(f"  (Loaded {extra} extra intent(s) from faq.json)")
    print("=" * 52)
    print(f"{BOT_NAME}: Hello! Welcome to {STORE_NAME}. How can I help you today?")
    session.state = "assisting"

    while True:
        try:
            user_input = input("\nYou: ")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{BOT_NAME}: Goodbye!")
            break
        try:
            reply, done = respond(user_input, session, intents, compiled)
        except Exception as exc:  # never crash the conversation
            reply, done = f"Sorry, something went wrong ({exc}). Please try again.", False
        print(f"{BOT_NAME}: {reply}")
        if done:
            session.state = "exit"
            break


if __name__ == "__main__":
    main()
