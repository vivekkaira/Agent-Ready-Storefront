# app.py
# Streamlit demo UI for the Agent-Ready Storefront.

import json
from datetime import datetime
import streamlit as st
import pandas as pd

from buyer_agent import pick_product
from catalog import get_product_by_id
from checkout import process_purchase
from growth_agent import suggest_upsell

AUDIT_LOG_FILE = "audit_log.json"

st.set_page_config(page_title="Agent-Ready Storefront", page_icon="🛒", layout="centered")


def log_to_audit_trail(entry):
    entry["timestamp"] = datetime.now().isoformat()
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        log = []
    log.append(entry)
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def reset_flow():
    for key in ["product", "pick_reason", "main_result", "upsell", "upsell_result", "user_request"]:
        st.session_state.pop(key, None)


# --- Init session state ---
if "main_result" not in st.session_state:
    st.session_state.main_result = None

st.title("🛒 Agent-Ready Storefront")
st.caption("AI Buyer Agent + Gated Razorpay Checkout + Growth Agent")

st.divider()

# --- Step 1: Ask what the user wants ---
with st.form("search_form"):
    user_request = st.text_input("What are you looking for?", value=st.session_state.get("user_request", ""))
    submitted = st.form_submit_button("🔍 Find product", type="primary")

if submitted:
    reset_flow()
    st.session_state.user_request = user_request
    with st.spinner("Agent is searching the catalog..."):
        pick = pick_product(user_request)
    if pick:
        product = get_product_by_id(pick["product_id"])
        st.session_state.product = product
        st.session_state.pick_reason = pick["reason"]
        log_to_audit_trail({
            "step": "product_selection",
            "status": "success",
            "user_request": user_request,
            "product": product["name"],
            "price": product["price"],
            "reason": pick["reason"]
        })
    else:
        st.error("Agent could not find a suitable product.")

# --- Step 2: Show the picked product ---
if st.session_state.get("product"):
    product = st.session_state.product
    st.subheader("Agent's pick")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{product['name']}**")
        st.markdown(f"_{st.session_state.pick_reason}_")
    with col2:
        st.markdown(f"### ₹{product['price']}")

    if st.session_state.get("main_result") is None:
        if st.button("✅ Proceed to checkout"):
            result = process_purchase(product)
            st.session_state.main_result = result
            log_to_audit_trail({"step": "checkout", "user_request": st.session_state.user_request, **result})
            st.rerun()

# --- Step 3: Handle checkout result (auto-approved, blocked, or needs approval) ---
if st.session_state.get("main_result"):
    result = st.session_state.main_result
    st.divider()
    st.subheader("Gate check + checkout")
    st.write(f"**Gate decision:** `{result['gate_decision']}`")
    st.write(f"**Reason:** {result['gate_reason']}")

    if result["status"] == "awaiting_approval":
        st.warning("This purchase exceeds the auto-approve limit and needs manual confirmation.")
        c1, c2 = st.columns(2)
        if c1.button("👍 Approve purchase"):
            final = process_purchase(st.session_state.product, approved=True)
            st.session_state.main_result = final
            log_to_audit_trail({"step": "checkout", "user_request": st.session_state.user_request, **final})
            st.rerun()
        if c2.button("👎 Reject purchase"):
            final = process_purchase(st.session_state.product, approved=False)
            st.session_state.main_result = final
            log_to_audit_trail({"step": "checkout", "user_request": st.session_state.user_request, **final})
            st.rerun()

    elif result["status"] == "failed_out_of_stock":
        st.error(f"❌ {result['gate_reason']} — no payment was attempted.")

    elif result["status"] == "rejected_by_user":
        st.info("Purchase was rejected. No payment was made.")

    elif result["status"] == "order_failed":
        st.error(f"⚠️ Order creation failed: {result.get('error', 'unknown error')}")

    elif result["status"] in ("order_created", "order_created_after_approval"):
        st.success(f"✅ Order created — Razorpay Order ID: `{result['order_id']}`")

        # --- Step 4: Growth agent upsell ---
        if "upsell" not in st.session_state:
            with st.spinner("Growth agent is looking for a complementary suggestion..."):
                upsell = suggest_upsell(st.session_state.product)
            st.session_state.upsell = upsell
            if upsell:
                log_to_audit_trail({
                    "step": "upsell_suggestion",
                    "based_on": st.session_state.product["name"],
                    "suggested_product": get_product_by_id(upsell["product_id"])["name"],
                    "pitch": upsell["pitch"]
                })

        upsell = st.session_state.get("upsell")
        if upsell:
            upsell_product = get_product_by_id(upsell["product_id"])
            st.divider()
            st.subheader("💡 Growth agent suggestion")
            st.markdown(f"**{upsell_product['name']}** — ₹{upsell_product['price']}")
            st.markdown(f"_{upsell['pitch']}_")

            if "upsell_result" not in st.session_state:
                c1, c2 = st.columns(2)
                if c1.button("➕ Add this too"):
                    final = process_purchase(upsell_product)
                    if final["status"] == "awaiting_approval":
                        final = process_purchase(upsell_product, approved=True)
                    st.session_state.upsell_result = final
                    log_to_audit_trail({"step": "upsell_checkout", **final})
                    st.rerun()
                if c2.button("No thanks"):
                    st.session_state.upsell_result = {"status": "declined_by_user"}
                    log_to_audit_trail({"step": "upsell_checkout", "product": upsell_product["name"], "status": "declined_by_user"})
                    st.rerun()
            else:
                ur = st.session_state.upsell_result
                if ur["status"] == "declined_by_user":
                    st.info("Upsell declined.")
                else:
                    st.success(f"✅ Upsell order created — Order ID: `{ur.get('order_id')}`")

if st.button("🔄 Start over"):
    reset_flow()
    st.session_state.main_result = None
    st.rerun()

# --- Audit trail ---
st.divider()
st.subheader("📋 Audit trail")

STATUS_STYLE = {
    "order_created": ("✅", "Order created"),
    "order_created_after_approval": ("✅", "Order created (after approval)"),
    "failed_out_of_stock": ("🚫", "Blocked — out of stock"),
    "rejected_by_user": ("❌", "Rejected by user"),
    "declined_by_user": ("➖", "Upsell declined"),
    "order_failed": ("⚠️", "Order failed"),
    "success": ("🔎", "Product selected"),
}

STEP_LABEL = {
    "product_selection": "Buyer agent",
    "checkout": "Checkout",
    "upsell_suggestion": "Growth agent",
    "upsell_checkout": "Upsell checkout",
}

try:
    with open(AUDIT_LOG_FILE, "r") as f:
        log = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    log = []

if not log:
    st.caption("No entries yet.")
else:
        # Newest first, show everything
    for entry in reversed(log):
            step = entry.get("step", "unknown")
            status = entry.get("status")
            icon, label = STATUS_STYLE.get(status, ("•", status or ""))
            step_label = STEP_LABEL.get(step, step)
            ts = entry.get("timestamp", "")
            time_str = ts.split("T")[1][:8] if "T" in ts else ts

            with st.container(border=True):
                c1, c2 = st.columns([1, 5])
                with c1:
                    st.markdown(f"### {icon}")
                with c2:
                    st.markdown(f"**{step_label}** &nbsp;·&nbsp; `{time_str}`")

                    if step == "product_selection":
                        st.write(f"Request: _\"{entry.get('user_request', '')}\"_")
                        if entry.get("product"):
                            st.write(f"Picked **{entry['product']}** (₹{entry.get('price', '?')}) — {entry.get('reason', '')}")

                    elif step in ("checkout", "upsell_checkout"):
                        if entry.get("product"):
                            st.write(f"**{entry['product']}** — ₹{entry.get('price', '?')}")
                        if entry.get("gate_reason"):
                            st.write(entry["gate_reason"])
                        if entry.get("order_id"):
                            st.caption(f"Razorpay order: `{entry['order_id']}`")

                    elif step == "upsell_suggestion":
                        st.write(f"Based on **{entry.get('based_on', '')}**, suggested **{entry.get('suggested_product', '')}**")
                        if entry.get("pitch"):
                            st.write(f"_{entry['pitch']}_")