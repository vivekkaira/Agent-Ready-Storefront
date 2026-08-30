# test_connection.py
# Quick sanity check: confirms Razorpay and Gemini keys both work
# before we build anything bigger.

import os
from dotenv import load_dotenv
import razorpay
from google import genai

# Load keys from .env file
load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("Testing Razorpay connection...")
try:
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    # Creating a tiny test order (amount is in paise, so 100 = ₹1)
    order = client.order.create({
        "amount": 100,
        "currency": "INR",
        "payment_capture": 1
    })
    print("Razorpay works! Test order created with ID:", order["id"])
except Exception as e:
    print("Razorpay connection failed:", e)

print("\nTesting Gemini connection...")
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Say hello in one short sentence."
    )
    print("Gemini works! Response:", response.text)
except Exception as e:
    print("Gemini connection failed:", e)