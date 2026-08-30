# main.py
# The full agentic commerce flow: AI buyer agent picks a product,
# it goes through a gate check, checkout happens via Razorpay,
# the growth agent suggests an upsell, and every step is logged
# to an audit trail.

import json
from datetime import datetime
from buyer_agent import pick_product
from catalog import get_product_by_id
from checkout import checkout_flow
from growth_agent import suggest_upsell

AUDIT_LOG_FILE = "audit_log.json"


def log_to_audit_trail(entry):
    """Appends one entry to the audit log file, creating it if needed."""
    entry["timestamp"] = datetime.now().isoformat()

    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = []

    log.append(entry)

    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def handle_purchase(product, user_request=None, is_upsell=False):
    """
    Runs one product through checkout, logs it, and returns the result.
    Used for both the original purchase and any accepted upsell.
    """
    label = "[Growth Agent]" if is_upsell else "[Agent]"
    print(f"\n{label} Running gate check + checkout for: {product['name']}...")

    result = checkout_flow(product)

    print(f"{label} Gate decision: {result['gate_decision']}")
    print(f"{label} Reason: {result['gate_reason']}")
    print(f"{label} Final status: {result['status']}")
    if result.get("order_id"):
        print(f"{label} Razorpay order ID: {result['order_id']}")

    log_to_audit_trail({
        "step": "upsell_checkout" if is_upsell else "checkout",
        "user_request": user_request,
        **result
    })

    return result


def run():
    print("=== Agent-Ready Storefront ===\n")
    user_request = input("What are you looking for? ")

    # Step 1: AI buyer agent picks a product
    print("\n[Agent] Searching catalog...")
    pick = pick_product(user_request)

    if not pick:
        print("[Agent] Could not find a suitable product.")
        log_to_audit_trail({
            "step": "product_selection",
            "status": "failed",
            "user_request": user_request
        })
        return

    product = get_product_by_id(pick["product_id"])
    if not product:
        print("[Agent] Picked an invalid product ID.")
        return

    print(f"[Agent] Picked: {product['name']} (₹{product['price']})")
    print(f"[Agent] Reason: {pick['reason']}")

    log_to_audit_trail({
        "step": "product_selection",
        "status": "success",
        "user_request": user_request,
        "product": product["name"],
        "price": product["price"],
        "reason": pick["reason"]
    })

    # Step 2: Gate check + checkout for the main product
    main_result = handle_purchase(product, user_request=user_request)

    # Step 3: Growth agent only fires if the main purchase actually succeeded
    if main_result["status"] in ("order_created", "order_created_after_approval"):
        print("\n[Growth Agent] Looking for a complementary suggestion...")
        upsell = suggest_upsell(product)

        if upsell:
            upsell_product = get_product_by_id(upsell["product_id"])
            if upsell_product:
                print(f"[Growth Agent] Suggestion: {upsell_product['name']} (₹{upsell_product['price']})")
                print(f"[Growth Agent] Pitch: {upsell['pitch']}")

                log_to_audit_trail({
                    "step": "upsell_suggestion",
                    "based_on": product["name"],
                    "suggested_product": upsell_product["name"],
                    "price": upsell_product["price"],
                    "pitch": upsell["pitch"]
                })

                answer = input("\nWould you like to add this too? (yes/no): ").strip().lower()
                if answer == "yes":
                    handle_purchase(upsell_product, is_upsell=True)
                else:
                    log_to_audit_trail({
                        "step": "upsell_checkout",
                        "product": upsell_product["name"],
                        "status": "declined_by_user"
                    })
            else:
                print("[Growth Agent] Suggested an invalid product ID, skipping.")
    else:
        print("\n[Growth Agent] Skipped — main purchase did not complete successfully.")

    print(f"\nFull audit trail saved to {AUDIT_LOG_FILE}")


if __name__ == "__main__":
    run()