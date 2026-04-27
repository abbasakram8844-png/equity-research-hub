import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Trade", page_icon="⚡", layout="wide")

# ---------- Header with refresh ----------
hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.title("⚡ Swing Trade Analysis — v2.0")
    st.caption("9-step framework • ₹2L capital • 2% risk rule • 4/6 checklist required")
with hcol2:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ---------- NSE session ----------
NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

@st.cache_resource
def get_nse_session():
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    try:
        s.get("https://www.nseindia.com/", timeout=10)
        time.sleep(0.5)
        s.get("https://www.nseindia.com/option-chain", timeout=10)
    except Exception:
        pass
    return s

@st.cache_data(ttl=600, show_spinner=False)
def fetch_quote(symbol: str):
    s = get_nse_session()
    sym = symbol.upper().strip()
    try:
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_history(symbol: str, days: int = 200):
    """Fetch daily price/volume history from NSE."""
    s = get_nse_session()
    sym = symbol.upper().strip()
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    url = (f"https://www.nseindia.com/api/historical/cm/equity"
           f"?symbol={sym}&series=[%22EQ%22]"
           f"&from={from_date.strftime('%d-%m-%Y')}"
           f"&to={to_date.strftime('%d-%m-%Y')}")
    try:
        r = s.get(url, timeout=20)
        if r.status_code == 200:
            data = r.json().get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            df["CH_TIMESTAMP"] = pd.to_datetime(df["CH_TIMESTAMP"])
            df = df.sort_values("CH_TIMESTAMP").reset_index(drop=True)
            df = df.rename(columns={
                "CH_OPENING_PRICE": "Open",
                "CH_TRADE_HIGH_PRICE": "High",
                "CH_TRADE_LOW_PRICE": "Low",
                "CH_CLOSING_PRICE": "Close",
                "CH_TOT_TRADED_QTY": "Volume",
            })
            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df.dropna(subset=["Close"])
    except Exception:
        pass
    return None

# ---------- Indicators ----------
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    h_l = df["High"] - df["Low"]
    h_c = (df["High"] - df["Close"].shift()).abs()
    l_c = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([h_l, h_c, l_c], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# ---------- Inputs ----------
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    ticker = st.text_input("Ticker", value="").strip().upper()
with col2:
    capital = st.number_input("Capital (₹)", min_value=10000, value=200000, step=10000)
with col3:
    risk_pct = st.slider("Risk per trade (%)", min_value=0.5, max_value=5.0, value=2.0, step=0.25)

if not ticker:
    st.info("👉 Enter a ticker to analyse a swing trade setup.")
    st.stop()

# ---------- Fetch ----------
with st.spinner(f"Fetching {ticker} from NSE…"):
    quote = fetch_quote(ticker)
    df = fetch_history(ticker, days=200)

if quote is None or df is None or len(df) < 50:
    st.error(
        "⚠️ Could not fetch data.\n\n"
        "**Possible reasons:**\n"
        "- Symbol misspelled\n"
        "- Stock is BSE-only\n"
        "- NSE rate-limited — click 🔄 Refresh in 30 seconds\n"
        "- Stock has less than 50 days of history"
    )
    st.stop()

# ---------- Compute indicators ----------
df["DMA20"] = df["Close"].rolling(20).mean()
df["DMA50"] = df["Close"].rolling(50).mean()
df["DMA200"] = df["Close"].rolling(200).mean() if len(df) >= 200 else np.nan
df["VolAvg20"] = df["Volume"].rolling(20).mean()
df["RSI"] = rsi(df["Close"])
df["ATR"] = atr(df)

last_row = df.iloc[-1]
prev_row = df.iloc[-2]

last_price = last_row["Close"]
last_high = last_row["High"]
last_low = last_row["Low"]
last_vol = last_row["Volume"]
dma20 = last_row["DMA20"]
dma50 = last_row["DMA50"]
dma200 = last_row["DMA200"]
vol_avg = last_row["VolAvg20"]
last_rsi = last_row["RSI"]
last_atr = last_row["ATR"]

# Recent levels
high_20d = df["High"].tail(20).max()
low_20d = df["Low"].tail(20).min()
high_60d = df["High"].tail(60).max()

# Quote data
info = quote.get("info", {}) or {}
company = info.get("companyName", ticker)
industry_info = quote.get("industryInfo", {}) or {}
basic_industry = industry_info.get("basicIndustry", "—")

# ---------- Display: Header ----------
st.success(f"✅ **{company}** ({ticker}) • {basic_industry}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{last_price:,.2f}",
          f"{(last_price - prev_row['Close']):+.2f} ({((last_price/prev_row['Close']-1)*100):+.2f}%)")
c2.metric("RSI (14)", f"{last_rsi:.1f}")
c3.metric("ATR (14)", f"₹{last_atr:.2f}")
c4.metric("Vol vs 20D Avg",
          f"{(last_vol/vol_avg)*100:.0f}%" if vol_avg else "—")

st.divider()

# ---------- 6-point pre-trade checklist ----------
st.subheader("✅ Pre-Trade Checklist (need 4 of 6 to pass)")

checks = []

# 1. Above 50 DMA (trend filter)
ok = last_price > dma50 if not pd.isna(dma50) else False
checks.append(("Price > 50 DMA (uptrend)", ok,
               f"₹{last_price:.2f} vs ₹{dma50:.2f}" if not pd.isna(dma50) else "—"))

# 2. 50 DMA > 200 DMA (long-term trend)
ok = (dma50 > dma200) if not pd.isna(dma200) else False
checks.append(("50 DMA > 200 DMA (long-term up)", ok,
               f"₹{dma50:.2f} vs ₹{dma200:.2f}" if not pd.isna(dma200) else "Not enough history"))

# 3. RSI between 40-70 (not overbought, not weak)
ok = 40 <= last_rsi <= 70
checks.append(("RSI 40–70 (healthy momentum)", ok, f"{last_rsi:.1f}"))

# 4. Volume surge (today's vol > 1.5× avg)
ok = (last_vol > 1.5 * vol_avg) if vol_avg else False
checks.append(("Volume > 1.5× 20D avg", ok,
               f"{(last_vol/vol_avg)*100:.0f}%" if vol_avg else "—"))

# 5. Near 20-day high (breakout setup)
dist_from_20d_high = ((last_price - high_20d) / high_20d) * 100
ok = dist_from_20d_high >= -2  # within 2% of 20D high
checks.append(("Within 2% of 20D high", ok, f"{dist_from_20d_high:+.1f}%"))

# 6. Higher highs structure (last 5 days)
hh = df["High"].tail(5).is_monotonic_increasing or (df["Close"].tail(5).iloc[-1] > df["Close"].tail(5).iloc[0])
checks.append(("Higher closes over last 5 days", bool(hh),
               f"₹{df['Close'].iloc[-5]:.2f} → ₹{last_price:.2f}"))

passed = sum(1 for _, ok, _ in checks if ok)

cols = st.columns(2)
for i, (name, ok, val) in enumerate(checks):
    icon = "✅" if ok else "❌"
    cols[i % 2].markdown(f"**{icon} {name}**  \n`{val}`")

st.metric("Checklist Score", f"{passed} / 6")

st.divider()

# ---------- Verdict ----------
st.subheader("🎯 Trade Setup")

if passed < 4:
    st.error(f"❌ **AVOID** — only {passed}/6 checklist items passed. Wait for a better setup.")
    st.stop()

# Setup is valid → calculate trade levels
risk_amount = capital * (risk_pct / 100)

# Entry options (dual)
entry_breakout = round(high_20d + (last_atr * 0.25), 2)  # break above 20D high
entry_pullback = round(dma20, 2) if not pd.isna(dma20) else round(last_price * 0.97, 2)

# Stop loss (ATR-based)
sl_breakout = round(entry_breakout - (last_atr * 1.5), 2)
sl_pullback = round(entry_pullback - (last_atr * 1.5), 2)

# Targets (1:2 and 1:3 R:R)
tgt1_breakout = round(entry_breakout + 2 * (entry_breakout - sl_breakout), 2)
tgt2_breakout = round(entry_breakout + 3 * (entry_breakout - sl_breakout), 2)
tgt1_pullback = round(entry_pullback + 2 * (entry_pullback - sl_pullback), 2)
tgt2_pullback = round(entry_pullback + 3 * (entry_pullback - sl_pullback), 2)

# Position sizing
qty_breakout = int(risk_amount / (entry_breakout - sl_breakout)) if entry_breakout > sl_breakout else 0
qty_pullback = int(risk_amount / (entry_pullback - sl_pullback)) if entry_pullback > sl_pullback else 0

# Show two setups side by side
st.markdown(f"**Risk per trade:** ₹{risk_amount:,.0f} ({risk_pct}% of ₹{capital:,})")

setup1, setup2 = st.columns(2)

with setup1:
    st.markdown("### 🚀 Setup A: Breakout Entry")
    st.metric("Entry (above 20D high)", f"₹{entry_breakout:,.2f}")
    st.metric("Stop Loss", f"₹{sl_breakout:,.2f}",
              f"-₹{entry_breakout - sl_breakout:.2f} risk per share")
    st.metric("Target 1 (1:2 R:R)", f"₹{tgt1_breakout:,.2f}")
    st.metric("Target 2 (1:3 R:R)", f"₹{tgt2_breakout:,.2f}")
    st.metric("Quantity", f"{qty_breakout} shares",
              f"₹{qty_breakout * entry_breakout:,.0f} capital")

with setup2:
    st.markdown("### 📉 Setup B: Pullback Entry")
    st.metric("Entry (at 20 DMA)", f"₹{entry_pullback:,.2f}")
    st.metric("Stop Loss", f"₹{sl_pullback:,.2f}",
              f"-₹{entry_pullback - sl_pullback:.2f} risk per share")
    st.metric("Target 1 (1:2 R:R)", f"₹{tgt1_pullback:,.2f}")
    st.metric("Target 2 (1:3 R:R)", f"₹{tgt2_pullback:,.2f}")
    st.metric("Quantity", f"{qty_pullback} shares",
              f"₹{qty_pullback * entry_pullback:,.0f} capital")

st.divider()

# ---------- Verdict ----------
if passed >= 5:
    st.success(f"✅ **STRONG BUY SETUP** — {passed}/6 checklist passed. High-conviction swing trade.")
else:
    st.warning(f"⚠️ **MODERATE SETUP** — {passed}/6 checklist passed. Trade with smaller size or wait for confirmation.")

st.divider()

# ---------- Price chart ----------
st.subheader("📊 Price Chart (with 20/50 DMA)")
chart_df = df.tail(120)[["CH_TIMESTAMP", "Close", "DMA20", "DMA50"]].set_index("CH_TIMESTAMP")
st.line_chart(chart_df)

st.divider()

# ---------- Quick links ----------
st.subheader("🔗 Quick Links")
ql1, ql2, ql3 = st.columns(3)
ql1.link_button("📊 Open on Tickertape",
                f"https://www.tickertape.in/stocks/{ticker.lower()}",
                use_container_width=True)
ql2.link_button("📈 NSE Live Quote",
                f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}",
                use_container_width=True)
ql3.link_button("📉 Open on Screener",
                f"https://www.screener.in/company/{ticker}/consolidated/",
                use_container_width=True)

st.caption(f"📌 Data: NSE India • {len(df)} days history • Cached 1 hour • Indicators: RSI(14), ATR(14), DMA(20/50/200)")
