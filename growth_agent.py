# growth_agent.py
# The growth agent: looks at what was just purchased and suggests
# one relevant upsell/cross-sell item from the catalog using Gemini.

import os
import json
from dotenv import load_dotenv
from google import genai
from catalog import get_catalog, get_product_by_id

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def suggest_upsell(purchased_product):
    """
    Given a product that was just bought, asks Gemini to suggest
    ONE complementary item from the catalog (not the same item).
    """
    catalog = get_catalog()
    # Exclude the item just bought from suggestions
    other_products = [p for p in catalog if p["id"] != purchased_product["id"]]

    prompt = f"""You are a growth agent for an online store. A customer just bought:

{json.dumps(purchased_product, indent=2)}

Here is the rest of the catalog (JSON):
{json.dumps(other_products, indent=2)}

Suggest ONE complementary product that pairs well with what they just bought
(e.g. accessories, related gear, or something commonly bought together).
Do NOT suggest something unrelated just because it's cheap.

Respond ONLY with valid JSON in this exact format, nothing else:
{{
  "product_id": "P00X",
  "pitch": "one short, friendly sentence suggesting this to the customer"
}}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()

    try:
        result = json.loads(text)
        return result
    except json.JSONDecodeError:
        print("Could not parse growth agent's response. Raw response:")
        print(text)
        return None


if __name__ == "__main__":
    # Quick standalone test
    test_product = get_product_by_id("P011")  # Yoga Mat
    result = suggest_upsell(test_product)
    if result:
        suggested = get_product_by_id(result["product_id"])
        print(f"Upsell suggestion: {suggested['name']} (₹{suggested['price']})")
        print(f"Pitch: {result['pitch']}")