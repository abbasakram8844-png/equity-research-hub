"""
Stock Analysis Page — GARP Framework
"""

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Stock Analysis", page_icon="📊", layout="wide")

if not st.session_state.get("password_correct", False):
    st.error("Please log in from the main page first.")
    st.stop()

st.title("📊 Stock Analysis — GARP Framework")
st.caption("8-point pre-screen + 9-step analysis for long-term investing")

col_a, col_b = st.columns([3, 1])
with col_a:
    ticker_input = st.text_input(
        "NSE/BSE Ticker (e.g., RELIANCE, TCS, BLS)",
        value="",
        help="Just type the symbol — we'll add .NS automatically",
    ).strip().upper()
with col_b:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"], index=0)

if not ticker_input:
    st.info("👆 Enter a ticker symbol to begin analysis.")
    st.stop()

suffix = ".NS" if exchange == "NSE" else ".BO"
full_ticker = f"{ticker_input}{suffix}"


@st.cache_data(ttl=300)
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        hist = stock.history(period="1y")
        return info, hist, None
    except Exception as e:
        return None, None, str(e)


with st.spinner(f"Fetching live data for {full_ticker}..."):
    info, hist, err = fetch_stock_data(full_ticker)

if err or not info or info.get("regularMarketPrice") is None:
    st.error(f"❌ Couldn't fetch data for **{full_ticker}**. Check the ticker or try the other exchange.")
    st.stop()

st.markdown("---")
st.subheader(f"💹 {info.get('longName', ticker_input)}")

price = info.get("regularMarketPrice", 0)
prev_close = info.get("previousClose", price)
change = price - prev_close
pct = (change / prev_close * 100) if prev_close else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{price:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,.2f}")
c3.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,.2f}")
mc = info.get("marketCap", 0) / 1e7
c4.metric("Market Cap", f"₹{mc:,.0f} Cr")

c5, c6, c7, c8 = st.columns(4)
c5.metric("P/E (TTM)", f"{info.get('trailingPE', 0):.2f}" if info.get("trailingPE") else "—")
c6.metric("P/B", f"{info.get('priceToBook', 0):.2f}" if info.get("priceToBook") else "—")
c7.metric("Sector", info.get("sector", "—"))
c8.metric("Industry", info.get("industry", "—"))

if hist is not None and not hist.empty:
    st.line_chart(hist["Close"], height=250)

st.markdown("---")
st.subheader("✅ 8-Point Pre-Screen Filter")
st.caption("Auto-fetched fields are pre-filled where available. Fill missing fields from Screener.in.")

roe_auto = (info.get("returnOnEquity", 0) or 0) * 100
de_auto = info.get("debtToEquity", 0) or 0
if de_auto > 5:
    de_auto = de_auto / 100
peg_auto = info.get("pegRatio", 0) or 0

with st.form("garp_form"):
    col1, col2 = st.columns(2)

    with col1:
        roce = st.number_input("ROCE % (latest)", value=0.0, step=0.5)
        roe_3y = st.number_input("ROE 3Y avg %", value=float(round(roe_auto, 1)), step=0.5)
        rev_cagr = st.number_input("Revenue CAGR 3Y %", value=0.0, step=0.5)
        promoter = st.number_input("Promoter Holding %", value=0.0, step=0.5)
        pledge = st.number_input("Promoter Pledge %", value=0.0, step=0.1)

    with col2:
        de_ratio = st.number_input("D/E Ratio", value=float(round(de_auto, 2)), step=0.1)
        ocf_pos_years = st.selectbox("OCF positive years (last 3Y)", [0, 1, 2, 3], index=2)
        fii_dii = st.number_input("FII + DII Holding %", value=0.0, step=0.5)
        peg = st.number_input("PEG Ratio", value=float(round(peg_auto, 2)), step=0.1)

    submitted = st.form_submit_button("🎯 Run GARP Analysis", type="primary")

if submitted:
    checks = [
        ("ROCE ≥ 20%", roce >= 20, f"{roce:.1f}%"),
        ("ROE 3Y ≥ 15%", roe_3y >= 15, f"{roe_3y:.1f}%"),
        ("Revenue CAGR 3Y ≥ 15%", rev_cagr >= 15, f"{rev_cagr:.1f}%"),
        ("Promoter > 50%", promoter > 50, f"{promoter:.1f}%"),
        ("Pledge = 0%", pledge == 0, f"{pledge:.1f}%"),
        ("D/E ≤ 0.5×", de_ratio <= 0.5, f"{de_ratio:.2f}×"),
        ("OCF positive ≥ 2 of 3 years", ocf_pos_years >= 2, f"{ocf_pos_years}/3"),
        ("FII + DII ≥ 1%", fii_dii >= 1, f"{fii_dii:.1f}%"),
        ("PEG ≤ 0.5", 0 < peg <= 0.5, f"{peg:.2f}"),
    ]

    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)

    st.markdown("---")
    st.subheader(f"📋 Pre-Screen Result: {passed}/{total} Passed")
    st.progress(passed / total)

    df = pd.DataFrame([
        {"Criterion": name, "Value": val, "Status": "✅ Pass" if ok else "❌ Fail"}
        for name, ok, val in checks
    ])
    st.dataframe(df, hide_index=True, use_container_width=True)

    conviction = round((passed / total) * 10, 1)

    st.markdown("---")
    st.subheader(f"🎯 Conviction Score: {conviction}/10")

    if passed >= 8:
        st.success(f"**STRONG BUY CANDIDATE** — {passed}/{total} criteria pass.")
    elif passed >= 6:
        st.info(f"**WATCHLIST** — {passed}/{total} criteria pass.")
    elif passed >= 4:
        st.warning(f"**CAUTIOUS** — Only {passed}/{total} criteria pass.")
    else:
        st.error(f"**AVOID** — {passed}/{total} criteria pass.")
