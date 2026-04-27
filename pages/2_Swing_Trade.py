import streamlit as st

st.set_page_config(page_title="Swing Trade", page_icon="⚡", layout="wide")

st.title("⚡ Swing Trade Calculator — v2.0")
st.caption("Manual entry calculator • Position sizing • Dual targets • No data API needed")

st.info(
    "💡 **How to use this page:**\n\n"
    "1. Find a swing setup on **Chartink** or **Tickertape** (pre-built scanners do this for you)\n"
    "2. Note the entry price, stop loss level, and the stock symbol\n"
    "3. Enter them below — get position size, targets, and risk in one click\n\n"
    "This page is intentionally manual: no broken APIs, no waiting, works every time."
)

st.divider()

# ---------- Inputs ----------
st.subheader("📝 Trade Inputs")

col1, col2 = st.columns(2)

with col1:
    ticker = st.text_input("Ticker (for labeling)", value="", placeholder="e.g. BLS").strip().upper()
    entry = st.number_input("Entry price (₹)", min_value=0.0, value=0.0, step=0.05, format="%.2f")
    stop_loss = st.number_input("Stop loss (₹)", min_value=0.0, value=0.0, step=0.05, format="%.2f")

with col2:
    capital = st.number_input("Total capital (₹)", min_value=10000, value=200000, step=10000)
    risk_pct = st.slider("Risk per trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.25)
    rr1 = st.number_input("Target 1 R:R", min_value=1.0, max_value=10.0, value=2.0, step=0.5)
    rr2 = st.number_input("Target 2 R:R", min_value=1.0, max_value=10.0, value=3.0, step=0.5)

# ---------- Validation ----------
if entry <= 0 or stop_loss <= 0:
    st.warning("👉 Enter both entry price and stop loss to calculate.")
    st.stop()

if stop_loss >= entry:
    st.error("⚠️ Stop loss must be **below** entry price for a long swing trade.")
    st.stop()

# ---------- Calculations ----------
risk_per_share = entry - stop_loss
risk_pct_of_entry = (risk_per_share / entry) * 100
risk_amount = capital * (risk_pct / 100)
quantity = int(risk_amount / risk_per_share)
capital_deployed = quantity * entry
capital_pct = (capital_deployed / capital) * 100

target_1 = round(entry + rr1 * risk_per_share, 2)
target_2 = round(entry + rr2 * risk_per_share, 2)
profit_at_t1 = quantity * (target_1 - entry)
profit_at_t2 = quantity * (target_2 - entry)
max_loss = quantity * risk_per_share

st.divider()

# ---------- Header ----------
label = ticker if ticker else "Trade"
st.success(f"✅ **{label}** — Trade plan calculated")

# ---------- Position summary ----------
st.subheader("📊 Position Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Entry", f"₹{entry:,.2f}")
c2.metric("Stop Loss", f"₹{stop_loss:,.2f}", f"-₹{risk_per_share:.2f} ({risk_pct_of_entry:.2f}%)")
c3.metric("Quantity", f"{quantity} shares")
c4.metric("Capital Deployed", f"₹{capital_deployed:,.0f}", f"{capital_pct:.1f}% of total")

st.divider()

# ---------- Risk ----------
st.subheader("⚠️ Risk")
c1, c2, c3 = st.columns(3)
c1.metric("Risk Amount", f"₹{risk_amount:,.0f}", f"{risk_pct}% of capital")
c2.metric("Max Loss (if SL hit)", f"₹{max_loss:,.0f}")
c3.metric("Risk per Share", f"₹{risk_per_share:.2f}")

st.divider()

# ---------- Targets ----------
st.subheader("🎯 Targets")
t1, t2 = st.columns(2)
with t1:
    st.markdown(f"### Target 1 — 1:{rr1:.1f} R:R")
    st.metric("Price", f"₹{target_1:,.2f}", f"+₹{target_1 - entry:.2f} ({((target_1/entry-1)*100):+.2f}%)")
    st.metric("Profit if hit", f"₹{profit_at_t1:,.0f}")
    st.caption(f"Suggested action: book 50% at this level")
with t2:
    st.markdown(f"### Target 2 — 1:{rr2:.1f} R:R")
    st.metric("Price", f"₹{target_2:,.2f}", f"+₹{target_2 - entry:.2f} ({((target_2/entry-1)*100):+.2f}%)")
    st.metric("Profit if hit", f"₹{profit_at_t2:,.0f}")
    st.caption(f"Suggested action: book remaining 50% or trail with stop")

st.divider()

# ---------- Trade card ----------
st.subheader("📋 Trade Card (copy to journal)")
trade_card = f"""
**{label}** — Swing Trade Plan

| Field | Value |
|---|---|
| Entry | ₹{entry:,.2f} |
| Stop Loss | ₹{stop_loss:,.2f} (-{risk_pct_of_entry:.2f}%) |
| Quantity | {quantity} shares |
| Capital Deployed | ₹{capital_deployed:,.0f} ({capital_pct:.1f}%) |
| Max Loss | ₹{max_loss:,.0f} ({risk_pct}% of ₹{capital:,}) |
| Target 1 (1:{rr1:.1f}) | ₹{target_1:,.2f} → ₹{profit_at_t1:,.0f} profit |
| Target 2 (1:{rr2:.1f}) | ₹{target_2:,.2f} → ₹{profit_at_t2:,.0f} profit |
"""
st.markdown(trade_card)

st.divider()

# ---------- Decision support ----------
st.subheader("🧠 Sanity Checks")

checks_passed = 0
total_checks = 4

if risk_pct_of_entry < 8:
    st.success(f"✅ **Stop loss is sensible** — {risk_pct_of_entry:.2f}% from entry (< 8%)")
    checks_passed += 1
else:
    st.warning(f"⚠️ **Wide stop** — {risk_pct_of_entry:.2f}% from entry. Consider tighter SL or smaller size.")

if capital_pct <= 25:
    st.success(f"✅ **Position size OK** — {capital_pct:.1f}% of capital (within 25% per trade)")
    checks_passed += 1
else:
    st.warning(f"⚠️ **Heavy position** — {capital_pct:.1f}% of capital in one trade. Consider reducing.")

if quantity > 0:
    st.success(f"✅ **Tradeable** — {quantity} shares fits the risk budget")
    checks_passed += 1
else:
    st.error(f"❌ **Risk too small** — risk amount can't buy even 1 share at this stop distance")

if rr1 >= 2.0:
    st.success(f"✅ **R:R meets minimum** — first target at 1:{rr1:.1f} (≥ 1:2)")
    checks_passed += 1
else:
    st.warning(f"⚠️ **Low R:R** — first target at 1:{rr1:.1f}, below 1:2 minimum")

st.metric("Sanity Score", f"{checks_passed} / {total_checks}")

if checks_passed == total_checks:
    st.success("🎯 **GO** — all sanity checks passed. Trade is structurally sound.")
elif checks_passed >= 3:
    st.warning("⚠️ **REVIEW** — most checks pass but one flag. Re-examine before entering.")
else:
    st.error("🛑 **RECONSIDER** — multiple flags. This setup may not fit your risk rules.")

st.divider()

# ---------- External chart links ----------
st.subheader("🔗 Chart & Research Links")
if ticker:
    ql1, ql2, ql3, ql4 = st.columns(4)
    ql1.link_button("📊 Tickertape Chart",
                    f"https://www.tickertape.in/stocks/{ticker.lower()}",
                    use_container_width=True)
    ql2.link_button("📈 Chartink",
                    f"https://chartink.com/stocks/{ticker.lower()}.html",
                    use_container_width=True)
    ql3.link_button("📉 Screener",
                    f"https://www.screener.in/company/{ticker}/consolidated/",
                    use_container_width=True)
    ql4.link_button("🏛️ NSE Quote",
                    f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}",
                    use_container_width=True)
else:
    st.caption("Enter a ticker above to see external chart links.")

st.caption("📌 Manual calculator • No external data dependencies • Works always")
