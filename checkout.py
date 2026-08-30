# checkout.py
# Takes a picked product, runs it through a spend-limit gate,
# and creates a real Razorpay test-mode order if approved.

import os
from dotenv import load_dotenv
import razorpay

load_dotenv()
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# --- Gate settings ---
AUTO_APPROVE_LIMIT = 7000  # ₹7000 — anything above this needs manual approval


def gate_check(product):
    """
    Decides whether this purchase can proceed automatically,
    needs approval, or should be blocked. Returns a decision dict.
    """
    price = product["price"]

    if price <= AUTO_APPROVE_LIMIT:
        return {
            "decision": "auto_approved",
            "reason": f"₹{price} is within the ₹{AUTO_APPROVE_LIMIT} auto-approve limit."
        }
    else:
        return {
            "decision": "needs_approval",
            "reason": f"₹{price} exceeds the ₹{AUTO_APPROVE_LIMIT} auto-approve limit. Manual confirmation required."
        }


def create_order(product):
    """
    Creates a Razorpay test-mode order for the given product.
    Amount must be in paise (₹1 = 100 paise).
    """
    amount_in_paise = product["price"] * 100

    order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1,
        "notes": {
            "product_id": product["id"],
            "product_name": product["name"]
        }
    })
    return order


def checkout_flow(product):
    """
    Full flow: stock check -> gate check -> (approve or block) -> create order.
    Returns a log entry dict describing what happened, for the audit trail.
    """
    log_entry = {
        "product": product["name"],
        "price": product["price"],
        "gate_decision": None,
        "gate_reason": None,
        "order_id": None,
        "status": None
    }

    # Step 0: stock check — fail gracefully if unavailable
    if product.get("stock", 0) <= 0:
        log_entry["gate_decision"] = "blocked"
        log_entry["gate_reason"] = f"'{product['name']}' is out of stock (0 units available)."
        log_entry["status"] = "failed_out_of_stock"
        print(f"\n❌ Sorry, '{product['name']}' is currently out of stock.")
        print("   No payment was attempted — order blocked before checkout.")
        return log_entry

    gate_result = gate_check(product)
    log_entry["gate_decision"] = gate_result["decision"]
    log_entry["gate_reason"] = gate_result["reason"]

    if gate_result["decision"] == "auto_approved":
        try:
            order = create_order(product)
            log_entry["order_id"] = order["id"]
            log_entry["status"] = "order_created"
        except Exception as e:
            log_entry["status"] = "order_failed"
            log_entry["error"] = str(e)
    else:
        print(f"\n⚠️  This purchase needs approval: {gate_result['reason']}")
        answer = input("Approve this purchase? (yes/no): ").strip().lower()
        if answer == "yes":
            try:
                order = create_order(product)
                log_entry["order_id"] = order["id"]
                log_entry["status"] = "order_created_after_approval"
            except Exception as e:
                log_entry["status"] = "order_failed"
                log_entry["error"] = str(e)
        else:
            log_entry["status"] = "rejected_by_user"

    return log_entry

def process_purchase(product, approved=None):
    """
    Non-interactive version of checkout_flow, for use in the UI.
    - If auto-approved: creates the order immediately.
    - If needs approval: only creates the order if approved=True was passed in.
      If approved is None, it just returns the gate decision without acting,
      so the UI can show an approve/reject button first.
    """
    log_entry = {
        "product": product["name"],
        "price": product["price"],
        "gate_decision": None,
        "gate_reason": None,
        "order_id": None,
        "status": None
    }

    if product.get("stock", 0) <= 0:
        log_entry["gate_decision"] = "blocked"
        log_entry["gate_reason"] = f"'{product['name']}' is out of stock (0 units available)."
        log_entry["status"] = "failed_out_of_stock"
        return log_entry

    gate_result = gate_check(product)
    log_entry["gate_decision"] = gate_result["decision"]
    log_entry["gate_reason"] = gate_result["reason"]

    if gate_result["decision"] == "auto_approved":
        try:
            order = create_order(product)
            log_entry["order_id"] = order["id"]
            log_entry["status"] = "order_created"
        except Exception as e:
            log_entry["status"] = "order_failed"
            log_entry["error"] = str(e)
        return log_entry

    # needs_approval case
    if approved is True:
        try:
            order = create_order(product)
            log_entry["order_id"] = order["id"]
            log_entry["status"] = "order_created_after_approval"
        except Exception as e:
            log_entry["status"] = "order_failed"
            log_entry["error"] = str(e)
    elif approved is False:
        log_entry["status"] = "rejected_by_user"
    else:
        log_entry["status"] = "awaiting_approval"

    return log_entry

if __name__ == "__main__":
    # Quick manual test with a fake product
    test_product = {"id": "P099", "name": "Test Item", "price": 2500}
    result = checkout_flow(test_product)
    print("\nLog entry:")
    print(result)