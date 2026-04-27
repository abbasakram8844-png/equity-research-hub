import streamlit as st
import requests
import time
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Watchlist", page_icon="👁️", layout="wide")

# ---------- Header with refresh ----------
hcol1, hcol2 = st.columns([5, 1])
with hcol1:
    st.title("👁️ Watchlist")
    st.caption("Live snapshot of your tracked stocks • Edit watchlist.txt in repo to add/remove")
with hcol2:
    st.write("")
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ---------- Load watchlist symbols ----------
@st.cache_data(ttl=60)
def load_watchlist():
    """Read watchlist.txt from repo root."""
    repo_root = Path(__file__).parent.parent
    wl_file = repo_root / "watchlist.txt"
    if not wl_file.exists():
        return []
    symbols = []
    for line in wl_file.read_text().splitlines():
        line = line.strip().upper()
        if line and not line.startswith("#"):
            symbols.append(line)
    return symbols

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
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# ---------- Load list ----------
symbols = load_watchlist()

if not symbols:
    st.error(
        "⚠️ `watchlist.txt` is empty or missing.\n\n"
        "Edit `watchlist.txt` in your GitHub repo root and add NSE symbols, one per line."
    )
    st.stop()

st.info(f"📋 Watching **{len(symbols)} stocks** • Edit `watchlist.txt` in GitHub to add/remove")

# ---------- Fetch all quotes ----------
progress = st.progress(0, text="Fetching live data from NSE…")
rows = []
failed = []

for i, sym in enumerate(symbols):
    quote = fetch_quote(sym)
    progress.progress((i + 1) / len(symbols), text=f"Fetched {i + 1}/{len(symbols)}: {sym}")
    if quote is None:
        failed.append(sym)
        continue

    info = quote.get("info", {}) or {}
    price = quote.get("priceInfo", {}) or {}
    industry_info = quote.get("industryInfo", {}) or {}

    last = price.get("lastPrice", 0) or 0
    pct = price.get("pChange", 0) or 0
    yhl = price.get("weekHighLow", {}) or {}
    y_high = yhl.get("max", 0) or 0
    y_low = yhl.get("min", 0) or 0
    pct_from_high = ((last - y_high) / y_high * 100) if y_high else 0
    pct_from_low = ((last - y_low) / y_low * 100) if y_low else 0

    rows.append({
        "Symbol": sym,
        "Company": (info.get("companyName", sym) or sym)[:40],
        "Price (₹)": last,
        "% Change": pct,
        "From 52W High %": pct_from_high,
        "From 52W Low %": pct_from_low,
        "52W High": y_high,
        "52W Low": y_low,
        "Industry": (industry_info.get("basicIndustry", "—") or "—")[:30],
    })

progress.empty()

if not rows:
    st.error("❌ Could not fetch any stock data. NSE may be rate-limiting. Click 🔄 Refresh in 30 seconds.")
    st.stop()

df = pd.DataFrame(rows)

# ---------- Color styling ----------
def color_pct_change(val):
    if val > 3:    return "background-color: #0a3d2e; color: #5dffac"
    if val > 0:    return "background-color: #1a3d2e; color: #8eff8e"
    if val < -3:   return "background-color: #4d1a1a; color: #ff7373"
    if val < 0:    return "background-color: #3d1f1f; color: #ffa3a3"
    return ""

def color_from_high(val):
    if val > -5:    return "background-color: #0a3d2e; color: #5dffac"  # near high
    if val < -30:   return "background-color: #4d1a1a; color: #ff7373"  # deep drawdown
    if val < -15:   return "background-color: #3d1f1f; color: #ffa3a3"
    return ""

# ---------- Master table ----------
st.subheader("📊 Live Watchlist (sortable — click any column header)")

styled = (df.style
          .format({
              "Price (₹)": "{:,.2f}",
              "% Change": "{:+.2f}%",
              "From 52W High %": "{:+.1f}%",
              "From 52W Low %": "{:+.1f}%",
              "52W High": "{:,.2f}",
              "52W Low": "{:,.2f}",
          })
          .map(color_pct_change, subset=["% Change"])
          .map(color_from_high, subset=["From 52W High %"]))

st.dataframe(styled, use_container_width=True, hide_index=True, height=420)

if failed:
    st.warning(f"⚠️ Could not fetch: **{', '.join(failed)}** — check the symbol or try Refresh")

st.divider()

# ---------- Quick filters ----------
st.subheader("🎯 Quick Filters")

f1, f2 = st.columns(2)

with f1:
    st.markdown("### 🔥 Hot Today (>3% gainers)")
    hot = df[df["% Change"] > 3].sort_values("% Change", ascending=False)
    if len(hot):
        for _, r in hot.iterrows():
            st.metric(f"{r['Symbol']} — {r['Company'][:25]}",
                      f"₹{r['Price (₹)']:,.2f}",
                      f"{r['% Change']:+.2f}%")
    else:
        st.caption("No stocks up >3% today")

with f2:
    st.markdown("### 📉 Big Drops (<-3% losers)")
    cold = df[df["% Change"] < -3].sort_values("% Change", ascending=True)
    if len(cold):
        for _, r in cold.iterrows():
            st.metric(f"{r['Symbol']} — {r['Company'][:25]}",
                      f"₹{r['Price (₹)']:,.2f}",
                      f"{r['% Change']:+.2f}%")
    else:
        st.caption("No stocks down >3% today")

st.divider()

f3, f4 = st.columns(2)

with f3:
    st.markdown("### 🎯 Near 52W High (within 5%)")
    near_high = df[df["From 52W High %"] > -5].sort_values("From 52W High %", ascending=False)
    if len(near_high):
        for _, r in near_high.iterrows():
            st.metric(f"{r['Symbol']} — {r['Company'][:25]}",
                      f"₹{r['Price (₹)']:,.2f}",
                      f"{r['From 52W High %']:+.1f}% from high")
    else:
        st.caption("No stocks within 5% of 52W high")

with f4:
    st.markdown("### 💎 Pulled Back 20%+ (GARP candidates)")
    pulled = df[df["From 52W High %"] < -20].sort_values("From 52W High %", ascending=True)
    if len(pulled):
        for _, r in pulled.iterrows():
            st.metric(f"{r['Symbol']} — {r['Company'][:25]}",
                      f"₹{r['Price (₹)']:,.2f}",
                      f"{r['From 52W High %']:+.1f}% from high")
    else:
        st.caption("No stocks pulled back 20%+")

st.divider()

# ---------- Summary stats ----------
st.subheader("📈 Watchlist Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocks Tracked", len(df))
c2.metric("Avg % Change", f"{df['% Change'].mean():+.2f}%")
c3.metric("Gainers", f"{(df['% Change'] > 0).sum()}")
c4.metric("Losers", f"{(df['% Change'] < 0).sum()}")

st.caption(f"📌 Data: NSE India • Cached 10 min • Tip: Click ‘🔍 Stock Analysis’ in sidebar to deep-dive any symbol")
