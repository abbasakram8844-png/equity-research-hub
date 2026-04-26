"""
Swing Trade Analysis Page — v2.0 Framework
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(page_title="Swing Trade", page_icon="📈", layout="wide")

if not st.session_state.get("password_correct", False):
    st.error("Please log in from the main page first.")
    st.stop()

st.title("⚡ Swing Trade Analysis — v2.0")
st.caption("9-step framework • ₹2L capital • 2% risk rule • 4/6 checklist required")

col_a, col_b, col_c = st.columns([2, 1, 1])
with col_a:
    ticker = st.text_input("Ticker", value="").strip().upper()
with col_b:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
with col_c:
    capital = st.number_input("Capital (₹)", value=200000, step=10000)

risk_pct = st.slider("Risk per trade (%)", 0.5, 5.0, 2.0, 0.5)

if not ticker:
    st.info("👆 Enter a ticker to analyse a swing trade setup.")
    st.stop()

suffix = ".NS" if exchange == "NSE" else ".BO"
full_ticker = f"{ticker}{suffix}"


@st.cache_data(ttl=300)
def fetch_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        info = stock.info
        return hist, info, None
    except Exception as e:
        return None, None, str(e)


with st.spinner("Fetching technicals..."):
    hist, info, err = fetch_data(full_ticker)

if err or hist is None or hist.empty:
    st.error(f"Couldn't fetch data for {full_ticker}.")
    st.stop()


def compute_indicators(df):
    df = df.copy()
    df["DMA50"] = df["Close"].rolling(50).mean()
    df["DMA200"] = df["Close"].rolling(200).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = tr.rolling(14).mean()

    df["High20"] = df["High"].rolling(20).max()
    df["Low20"] = df["Low"].rolling(20).min()
    df["AvgVol20"] = df["Volume"].rolling(20).mean()

    return df


df = compute_indicators(hist)
last = df.iloc[-1]
price = last["Close"]
dma50 = last["DMA50"]
dma200 = last["DMA200"]
rsi = last["RSI"]
atr = last["ATR"]
high20 = last["High20"]
low20 = last["Low20"]
vol_today = last["Volume"]
avg_vol = last["AvgVol20"]

st.markdown("---")
st.subheader(f"📊 {info.get('longName', ticker)}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{price:,.2f}")
c2.metric("50 DMA", f"{dma50:,.2f}" if not np.isnan(dma50) else "—")
c3.metric("200 DMA", f"{dma200:,.2f}" if not np.isnan(dma200) else "—")
c4.metric("RSI (14)", f"{rsi:.1f}" if not np.isnan(rsi) else "—")

c5, c6, c7, c8 = st.columns(4)
c5.metric("ATR (14)", f"{atr:.2f}" if not np.isnan(atr) else "—")
c6.metric("20D High", f"{high20:,.2f}")
c7.metric("20D Low", f"{low20:,.2f}")
c8.metric("Vol vs 20D Avg", f"{(vol_today/avg_vol):.2f}×" if avg_vol else "—")

st.line_chart(df[["Close", "DMA50", "DMA200"]].dropna(), height=300)

st.markdown("---")
st.subheader("✅ Pre-Trade Checklist (need 4/6 to pass)")

checks = [
    ("Above 50 DMA", price > dma50 if not np.isnan(dma50) else False),
    ("Above 200 DMA", price > dma200 if not np.isnan(dma200) else False),
    ("RSI between 40–70", 40 <= rsi <= 70 if not np.isnan(rsi) else False),
    ("Volume > 1.2× 20D avg", vol_today > 1.2 * avg_vol if avg_vol else False),
    ("Within 5% of 20D high", price >= 0.95 * high20),
    ("ATR healthy (1–5% of price)", 0.01 * price <= atr <= 0.05 * price if not np.isnan(atr) else False),
]

passed = sum(1 for _, ok in checks if ok)

cdf = pd.DataFrame([{"Check": name, "Status": "✅" if ok else "❌"} for name, ok in checks])
st.dataframe(cdf, hide_index=True, use_container_width=True)

if passed >= 4:
    st.success(f"**{passed}/6 PASSED — Setup qualifies for trade planning.**")
else:
    st.warning(f"**{passed}/6 PASSED — Setup does NOT qualify. Skip this trade.**")

st.markdown("---")
st.subheader("🎯 Trade Plan")

entry_a = round(high20 * 1.005, 2)
sl_a = round(entry_a - (1.5 * atr), 2) if not np.isnan(atr) else 0
target_a1 = round(entry_a + (2 * atr), 2) if not np.isnan(atr) else 0
target_a2 = round(entry_a + (3 * atr), 2) if not np.isnan(atr) else 0

entry_b = round(dma50 * 1.005, 2) if not np.isnan(dma50) else 0
sl_b = round(entry_b - (1.5 * atr), 2) if not np.isnan(atr) else 0
target_b1 = round(entry_b + (2 * atr), 2) if not np.isnan(atr) else 0
target_b2 = round(entry_b + (3 * atr), 2) if not np.isnan(atr) else 0

trade_data = pd.DataFrame([
    {
        "Setup": "A: Breakout (>20D high)",
        "Entry": f"₹{entry_a:,.2f}",
        "Stop Loss": f"₹{sl_a:,.2f}",
        "Target 1 (2R)": f"₹{target_a1:,.2f}",
        "Target 2 (3R)": f"₹{target_a2:,.2f}",
        "R:R": f"1:{(target_a1-entry_a)/(entry_a-sl_a):.1f}" if entry_a > sl_a else "—",
    },
    {
        "Setup": "B: Pullback (near 50 DMA)",
        "Entry": f"₹{entry_b:,.2f}",
        "Stop Loss": f"₹{sl_b:,.2f}",
        "Target 1 (2R)": f"₹{target_b1:,.2f}",
        "Target 2 (3R)": f"₹{target_b2:,.2f}",
        "R:R": f"1:{(target_b1-entry_b)/(entry_b-sl_b):.1f}" if entry_b > sl_b else "—",
    },
])
st.dataframe(trade_data, hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("💰 Position Sizing")

max_loss = capital * (risk_pct / 100)
st.metric(f"Max loss per trade ({risk_pct}% of ₹{capital:,})", f"₹{max_loss:,.0f}")

col_x, col_y = st.columns(2)
with col_x:
    st.markdown("**Setup A (Breakout)**")
    if entry_a > sl_a:
        risk_per_share_a = entry_a - sl_a
        qty_a = int(max_loss / risk_per_share_a)
        capital_used_a = qty_a * entry_a
        st.write(f"Risk per share: ₹{risk_per_share_a:.2f}")
        st.write(f"**Qty: {qty_a} shares**")
        st.write(f"Capital deployed: ₹{capital_used_a:,.0f}")
        st.write(f"% of capital: {capital_used_a/capital*100:.1f}%")

with col_y:
    st.markdown("**Setup B (Pullback)**")
    if entry_b > sl_b:
        risk_per_share_b = entry_b - sl_b
        qty_b = int(max_loss / risk_per_share_b)
        capital_used_b = qty_b * entry_b
        st.write(f"Risk per share: ₹{risk_per_share_b:.2f}")
        st.write(f"**Qty: {qty_b} shares**")
        st.write(f"Capital deployed: ₹{capital_used_b:,.0f}")
        st.write(f"% of capital: {capital_used_b/capital*100:.1f}%")

st.markdown("---")
if passed >= 4 and entry_a > sl_a:
    st.success("**FINAL VERDICT: TRADE QUALIFIES**")
else:
    st.error("**FINAL VERDICT: SKIP** — Setup doesn't meet 4/6 threshold.")
