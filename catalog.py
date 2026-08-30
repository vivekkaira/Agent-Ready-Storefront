# catalog.py
# Pulls a real, structured product catalog from DummyJSON's free API
# and reshapes it to match our store's format. Caches locally so we
# don't re-fetch on every run.

import json
import os
import requests

CACHE_FILE = "catalog_cache.json"
USD_TO_INR = 83  # rough conversion, good enough for a demo

API_URL = "https://dummyjson.com/products?limit=100"


def _fetch_from_api():
    """Fetches products from DummyJSON and reshapes them to our schema."""
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()
    data = response.json()

    catalog = []
    for item in data["products"]:
        price_inr = round(item["price"] * USD_TO_INR)
        catalog.append({
            "id": f"P{item['id']:03d}",
            "name": item["title"],
            "price": price_inr,
            "category": item["category"],
            "stock": item["stock"],
            "description": item["description"],
            "brand": item.get("brand", "Generic"),
            "rating": item.get("rating", 0),
            "thumbnail": item.get("thumbnail", "")
        })
    return catalog


def _load_catalog():
    """Loads catalog from local cache if present, otherwise fetches fresh."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)

    catalog = _fetch_from_api()
    with open(CACHE_FILE, "w") as f:
        json.dump(catalog, f, indent=2)
    return catalog


CATALOG = _load_catalog()


def get_catalog():
    """Returns the full product catalog."""
    return CATALOG

def get_product_by_id(product_id):
    """Finds a single product by its ID, or returns None."""
    for product in CATALOG:
        if product["id"] == product_id:
            return product
    return None

def get_products_by_category(category):
    """Returns all products in a given category."""
    return [p for p in CATALOG if p["category"] == category]

def refresh_catalog():
    """Force re-fetch from the API, ignoring the cache."""
    global CATALOG
    catalog = _fetch_from_api()
    with open(CACHE_FILE, "w") as f:
        json.dump(catalog, f, indent=2)
    CATALOG = catalog
    return CATALOG