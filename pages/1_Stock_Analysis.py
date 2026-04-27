import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Stock Analysis", page_icon="📈", layout="wide")

st.title("📈 Stock Analysis — GARP Framework")
st.caption("8-point pre-screen → 9-step GARP analysis → Conviction Score 1–10")

# ---------- Cached data fetcher with retry ----------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock(symbol: str):
    """Fetch ticker info + history with retries. Returns (info, hist, source)."""
    last_err = None
    for suffix in [".NS", ".BO"]:
        ticker_symbol = symbol.upper().strip() + suffix
        for attempt in range(3):
            try:
                tk = yf.Ticker(ticker_symbol)
                info = tk.info
                hist = tk.history(period="1y")
                if info and hist is not None and not hist.empty and info.get("regularMarketPrice") is not None:
                    return info, hist, ticker_symbol
            except Exception as e:
                last_err = str(e)
            time.sleep(1.5 * (attempt + 1))
    return None, None, last_err

# ---------- Input ----------
col_in1, col_in2 = st.columns([3, 1])
with col_in1:
    symbol = st.text_input(
        "Enter NSE/BSE symbol (no suffix needed)",
        value="RELIANCE",
        help="Examples: RELIANCE, BLS, AVANTEL, TCS"
    )
with col_in2:
    st.write("")
    st.write("")
    go = st.button("🔍 Analyze", type="primary", use_container_width=True)

if not go:
    st.info("Enter a symbol and click Analyze.")
    st.stop()

# ---------- Fetch ----------
with st.spinner(f"Fetching data for {symbol}…"):
    info, hist, source = fetch_stock(symbol)

if info is None:
    st.error(
        "⚠️ Yahoo Finance is rate-limiting Streamlit Cloud right now.\n\n"
        "**What to do:**\n"
        "- Wait 2–5 minutes and try again\n"
        "- Or try a different symbol\n\n"
        f"Technical detail: `{source}`"
    )
    st.stop()

st.success(f"✅ Loaded: **{info.get('longName', symbol)}** (`{source}`)")

# ---------- Header metrics ----------
price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
prev_close = info.get("previousClose") or price
change = price - prev_close
change_pct = (change / prev_close * 100) if prev_close else 0
mcap_cr = (info.get("marketCap") or 0) / 1e7

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{price:,.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
c2.metric("Market Cap", f"₹{mcap_cr:,.0f} Cr")
c3.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,.2f}")
c4.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,.2f}")

st.divider()

# ---------- 8-point pre-screen ----------
st.subheader("🎯 8-Point Pre-Screen")

pe = info.get("trailingPE")
roe = (info.get("returnOnEquity") or 0) * 100
debt_to_equity = (info.get("debtToEquity") or 0) / 100
profit_margin = (info.get("profitMargins") or 0) * 100
rev_growth = (info.get("revenueGrowth") or 0) * 100
peg = info.get("pegRatio")

checks = [
    ("ROE ≥ 15%",            roe >= 15,              f"{roe:.1f}%"),
    ("D/E ≤ 0.5×",           debt_to_equity <= 0.5,  f"{debt_to_equity:.2f}"),
    ("Profit Margin > 10%",  profit_margin > 10,     f"{profit_margin:.1f}%"),
    ("Revenue Growth > 15%", rev_growth > 15,        f"{rev_growth:.1f}%"),
    ("PE Ratio < 40",        bool(pe) and pe < 40,   f"{pe:.1f}" if pe else "N/A"),
    ("PEG ≤ 0.5",            bool(peg) and peg <= 0.5, f"{peg:.2f}" if peg else "N/A"),
]

passed = sum(1 for _, ok, _ in checks if ok)

cols = st.columns(3)
for i, (name, ok, val) in enumerate(checks):
    icon = "✅" if ok else "❌"
    cols[i % 3].markdown(f"**{icon} {name}**  \n`{val}`")

st.metric("Pre-Screen Score", f"{passed} / {len(checks)}")

if passed >= 5:
    st.success("✅ Strong candidate — proceed to full GARP analysis")
elif passed >= 3:
    st.warning("⚠️ Mixed signals — investigate further")
else:
    st.error("❌ Weak candidate — likely a pass")

st.divider()

# ---------- Price chart ----------
st.subheader("📊 1-Year Price Chart")
if hist is not None and not hist.empty:
    st.line_chart(hist["Close"])
else:
    st.info("Price history unavailable.")

st.divider()

# ---------- Key fundamentals table ----------
st.subheader("📋 Key Fundamentals")
fundamentals = {
    "Sector":                 info.get("sector", "—"),
    "Industry":               info.get("industry", "—"),
    "PE (TTM)":               f"{pe:.2f}" if pe else "—",
    "PB":                     f"{info.get('priceToBook', 0):.2f}",
    "ROE":                    f"{roe:.2f}%",
    "Debt/Equity":            f"{debt_to_equity:.2f}",
    "Profit Margin":          f"{profit_margin:.2f}%",
    "Revenue Growth (YoY)":   f"{rev_growth:.2f}%",
    "Dividend Yield":         f"{(info.get('dividendYield') or 0)*100:.2f}%",
    "Beta":                   f"{info.get('beta', 0):.2f}",
}
st.dataframe(
    pd.DataFrame(fundamentals.items(), columns=["Metric", "Value"]),
    use_container_width=True, hide_index=True
)

st.caption("📌 Data: Yahoo Finance • Cached 1 hour • Conviction score & full 9-step GARP coming in Phase 2")
