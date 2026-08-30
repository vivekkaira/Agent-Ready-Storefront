# buyer_agent.py
# The AI buyer agent: takes a plain-English request, looks at the
# catalog, and picks the best matching product using Gemini.

import os
import json
from dotenv import load_dotenv
from google import genai
from catalog import get_catalog

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def pick_product(user_request):
    """
    Sends the user's request + catalog to Gemini, asks it to pick
    the single best matching product, and returns structured data.
    """
    catalog = get_catalog()

    prompt = f"""You are a shopping assistant agent. A customer wants to buy something.

Customer request: "{user_request}"

Here is the store's catalog (JSON):
{json.dumps(catalog, indent=2)}

Pick the ONE best matching product for the customer's request.
Respond ONLY with valid JSON in this exact format, nothing else:
{{
  "product_id": "P00X",
  "reason": "short one-sentence reason why this matches"
}}
If nothing matches well, still pick the closest option.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    # Clean up response in case Gemini wraps it in markdown code fences
    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    try:
        result = json.loads(text)
        return result
    except json.JSONDecodeError:
        print("Could not parse Gemini's response as JSON. Raw response:")
        print(text)
        return None


if __name__ == "__main__":
    user_request = input("What are you looking for? ")
    result = pick_product(user_request)

    if result:
        product_id = result.get("product_id")
        reason = result.get("reason")

        from catalog import get_product_by_id
        product = get_product_by_id(product_id)

        if product:
            print(f"\nAgent picked: {product['name']} (₹{product['price']})")
            print(f"Reason: {reason}")
        else:
            print(f"\nAgent returned an unknown product ID: {product_id}")