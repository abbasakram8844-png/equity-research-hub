import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Trade", page_icon="⚡", layout="wide")

# ---------- Header ----------
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
    "Referer": "https://www.nseindia.com/get-quotes/equity",
}

@st.cache_resource
def get_nse_session():
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    try:
        s.get("https://www.nseindia.com/", timeout=10)
        time.sleep(0.5)
        s.get("https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE", timeout=10)
        time.sleep(0.3)
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
def fetch_history(symbol: str):
    """NSE's own chart endpoint — returns ~1yr of intraday data we resample to daily."""
    s = get_nse_session()
    sym = symbol.upper().strip()
    last_err = "Unknown error"
    for attempt in range(3):
        try:
            r = s.get(f"https://www.nseindia.com/api/chart-databyindex?index={sym}EQN",
                      timeout=20)
            if r.status_code == 200:
                data = r.json()
                grph = data.get("grapthData", [])
                if not grph or len(grph) < 50:
                    last_err = f"Only {len(grph)} data points returned"
                    time.sleep(1)
                    continue
                df = pd.DataFrame(grph, columns=["ts", "Close"])
                df["Date"] = pd.to_datetime(df["ts"], unit="ms")
                df = df[["Date", "Close"]]
                # Resample intraday → daily (last close of each trading day)
                df_daily = df.set_index("Date").resample("D").last().dropna().reset_index()
                # Approximate OHLV from intraday min/max per day
                df_intra = df.set_index("Date")
                ohlc = df_intra["Close"].resample("D").agg(["first", "max", "min", "last"])
                ohlc.columns = ["Open", "High", "Low", "Close"]
                ohlc = ohlc.dropna().reset_index()
                # Volume: not in this endpoint — set to 0 (we'll handle in checklist)
                ohlc["Volume"] = 0
                return ohlc.tail(250)
            else:
                last_err = f"HTTP {r.status_code}"
        except Exception as e:
            last_err = str(e)[:80]
        time.sleep(1.5)
    return None, last_err

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_history_safe(symbol: str):
    result = fetch_history(symbol)
    if isinstance(result, tuple):
        return None, result[1]
    return result, None

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
    ticker = st.text_input("Ticker (NSE symbol, no suffix)", value="").strip().upper()
with col2:
    capital = st.number_input("Capital (₹)", min_value=10000, value=200000, step=10000)
with col3:
    risk_pct = st.slider("Risk per trade (%)", 0.5, 5.0, 2.0, 0.25)

if not ticker:
    st.info("👉 Enter a ticker to analyse a swing trade setup.")
    st.stop()

# ---------- Fetch ----------
with st.spinner(f"Fetching {ticker}…"):
    quote = fetch_quote(ticker)
    df, err = fetch_history_safe(ticker)

if df is None or len(df) < 50:
    st.error(
        f"⚠️ Could not fetch historical data.\n\n"
        f"**Error detail:** `{err or 'no data'}`\n\n"
        f"**Try:**\n"
        f"- Click 🔄 Refresh and retry in 30 seconds\n"
        f"- Try a different symbol (RELIANCE, TCS, INFY)\n"
        f"- If all fail, NSE chart endpoint is blocked — we'll need plan C"
    )
    st.stop()

# ---------- Indicators ----------
df["DMA20"] = df["Close"].rolling(20).mean()
df["DMA50"] = df["Close"].rolling(50).mean()
df["DMA200"] = df["Close"].rolling(200).mean() if len(df) >= 200 else np.nan
df["RSI"] = rsi(df["Close"])
df["ATR"] = atr(df)

last = df.iloc[-1]
prev = df.iloc[-2]
last_price = last["Close"]
dma20 = last["DMA20"]
dma50 = last["DMA50"]
dma200 = last["DMA200"]
last_rsi = last["RSI"]
last_atr = last["ATR"]
high_20d = df["High"].tail(20).max()

# ---------- Quote info ----------
if quote:
    info = quote.get("info", {}) or {}
    company = info.get("companyName", ticker)
    industry_info = quote.get("industryInfo", {}) or {}
    basic_industry = industry_info.get("basicIndustry", "—")
    pinfo = quote.get("priceInfo", {}) or {}
    live_price = pinfo.get("lastPrice", last_price) or last_price
    live_change = pinfo.get("change", 0) or 0
    live_pct = pinfo.get("pChange", 0) or 0
else:
    company = ticker
    basic_industry = "—"
    live_price = last_price
    live_change = last_price - prev["Close"]
    live_pct = ((last_price / prev["Close"]) - 1) * 100

st.success(f"✅ **{company}** ({ticker}) • {basic_industry}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{live_price:,.2f}", f"{live_change:+.2f} ({live_pct:+.2f}%)")
c2.metric("RSI (14)", f"{last_rsi:.1f}")
c3.metric("ATR (14)", f"₹{last_atr:.2f}")
c4.metric("History days", f"{len(df)}")

st.divider()

# ---------- 5-point checklist (volume removed since unavailable) ----------
st.subheader("✅ Pre-Trade Checklist (need 3 of 5 to pass)")

checks = []

ok = last_price > dma50 if not pd.isna(dma50) else False
checks.append(("Price > 50 DMA (uptrend)", ok,
               f"₹{last_price:.2f} vs ₹{dma50:.2f}" if not pd.isna(dma50) else "—"))

ok = (dma50 > dma200) if not pd.isna(dma200) else False
checks.append(("50 DMA > 200 DMA (long-term up)", ok,
               f"₹{dma50:.2f} vs ₹{dma200:.2f}" if not pd.isna(dma200) else "Not enough history"))

ok = 40 <= last_rsi <= 70
checks.append(("RSI 40–70 (healthy momentum)", ok, f"{last_rsi:.1f}"))

dist = ((last_price - high_20d) / high_20d) * 100
ok = dist >= -2
checks.append(("Within 2% of 20D high", ok, f"{dist:+.1f}%"))

hh = df["Close"].tail(5).iloc[-1] > df["Close"].tail(5).iloc[0]
checks.append(("Higher closes over last 5 days", bool(hh),
               f"₹{df['Close'].iloc[-5]:.2f} → ₹{last_price:.2f}"))

passed = sum(1 for _, ok, _ in checks if ok)

cols = st.columns(2)
for i, (name, ok, val) in enumerate(checks):
    icon = "✅" if ok else "❌"
    cols[i % 2].markdown(f"**{icon} {name}**  \n`{val}`")

st.metric("Checklist Score", f"{passed} / 5")

st.info("ℹ️ Volume check disabled — NSE chart endpoint doesn't expose volume. "
        "For volume-confirmed setups, cross-check on Tickertape or Chartink.")

st.divider()

# ---------- Verdict ----------
st.subheader("🎯 Trade Setup")

if passed < 3:
    st.error(f"❌ **AVOID** — only {passed}/5 passed. Wait for better setup.")
    st.stop()

risk_amount = capital * (risk_pct / 100)

entry_breakout = round(high_20d + (last_atr * 0.25), 2)
entry_pullback = round(dma20, 2) if not pd.isna(dma20) else round(last_price * 0.97, 2)
sl_breakout = round(entry_breakout - (last_atr * 1.5), 2)
sl_pullback = round(entry_pullback - (last_atr * 1.5), 2)
tgt1_b = round(entry_breakout + 2 * (entry_breakout - sl_breakout), 2)
tgt2_b = round(entry_breakout + 3 * (entry_breakout - sl_breakout), 2)
tgt1_p = round(entry_pullback + 2 * (entry_pullback - sl_pullback), 2)
tgt2_p = round(entry_pullback + 3 * (entry_pullback - sl_pullback), 2)
qty_b = int(risk_amount / (entry_breakout - sl_breakout)) if entry_breakout > sl_breakout else 0
qty_p = int(risk_amount / (entry_pullback - sl_pullback)) if entry_pullback > sl_pullback else 0

st.markdown(f"**Risk per trade:** ₹{risk_amount:,.0f} ({risk_pct}% of ₹{capital:,})")

s1, s2 = st.columns(2)
with s1:
    st.markdown("### 🚀 Setup A: Breakout")
    st.metric("Entry (above 20D high)", f"₹{entry_breakout:,.2f}")
    st.metric("Stop Loss", f"₹{sl_breakout:,.2f}", f"-₹{entry_breakout - sl_breakout:.2f} risk/share")
    st.metric("Target 1 (1:2)", f"₹{tgt1_b:,.2f}")
    st.metric("Target 2 (1:3)", f"₹{tgt2_b:,.2f}")
    st.metric("Quantity", f"{qty_b} shares", f"₹{qty_b * entry_breakout:,.0f} capital")
with s2:
    st.markdown("### 📉 Setup B: Pullback")
    st.metric("Entry (at 20 DMA)", f"₹{entry_pullback:,.2f}")
    st.metric("Stop Loss", f"₹{sl_pullback:,.2f}", f"-₹{entry_pullback - sl_pullback:.2f} risk/share")
    st.metric("Target 1 (1:2)", f"₹{tgt1_p:,.2f}")
    st.metric("Target 2 (1:3)", f"₹{tgt2_p:,.2f}")
    st.metric("Quantity", f"{qty_p} shares", f"₹{qty_p * entry_pullback:,.0f} capital")

st.divider()

if passed >= 4:
    st.success(f"✅ **STRONG BUY SETUP** — {passed}/5 passed")
else:
    st.warning(f"⚠️ **MODERATE SETUP** — {passed}/5 passed. Smaller size or wait.")

st.divider()

# ---------- Chart ----------
st.subheader("📊 Price Chart (with 20/50 DMA)")
chart_df = df.tail(120)[["Date", "Close", "DMA20", "DMA50"]].set_index("Date")
st.line_chart(chart_df)

st.divider()

st.subheader("🔗 Quick Links")
ql1, ql2, ql3 = st.columns(3)
ql1.link_button("📊 Tickertape",
                f"https://www.tickertape.in/stocks/{ticker.lower()}", use_container_width=True)
ql2.link_button("📈 Chartink Scanner",
                f"https://chartink.com/stocks/{ticker.lower()}.html", use_container_width=True)
ql3.link_button("📉 Screener",
                f"https://www.screener.in/company/{ticker}/consolidated/", use_container_width=True)

st.caption(f"📌 NSE chart-databyindex • {len(df)} daily bars • Cached 1hr")
