import streamlit as st
import requests
import time
import pandas as pd

st.set_page_config(page_title="Sector Heatmap", page_icon="🏭", layout="wide")

st.title("🏭 Sector Heatmap")
st.caption("Live performance of Nifty sectoral indices — direct from NSE")

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
        s.get("https://www.nseindia.com/market-data/live-equity-market", timeout=10)
    except Exception:
        pass
    return s

@st.cache_data(ttl=600, show_spinner=False)
def fetch_all_indices():
    """Fetch all NSE indices in one call."""
    s = get_nse_session()
    try:
        r = s.get("https://www.nseindia.com/api/allIndices", timeout=15)
        if r.status_code == 200:
            return r.json().get("data", [])
    except Exception:
        pass
    return []

# ---------- Sector indices we care about ----------
SECTOR_INDICES = [
    "NIFTY BANK", "NIFTY IT", "NIFTY AUTO", "NIFTY PHARMA",
    "NIFTY FMCG", "NIFTY METAL", "NIFTY ENERGY", "NIFTY REALTY",
    "NIFTY MEDIA", "NIFTY PSU BANK", "NIFTY PVT BANK",
    "NIFTY FIN SERVICE", "NIFTY HEALTHCARE INDEX",
    "NIFTY CONSUMER DURABLES", "NIFTY OIL & GAS",
]

BROAD_INDICES = ["NIFTY 50", "NIFTY NEXT 50", "NIFTY MIDCAP 100", "NIFTY SMALLCAP 100"]

# ---------- Fetch ----------
with st.spinner("Fetching live sector data from NSE…"):
    all_data = fetch_all_indices()

if not all_data:
    st.error("⚠️ Could not fetch from NSE. Try refreshing in 30 seconds.")
    st.stop()

# Build lookup
index_map = {row.get("index", ""): row for row in all_data}

# ---------- Broad markets ----------
st.subheader("📅 Today's Snapshot — Broad Markets")
cols = st.columns(len(BROAD_INDICES))
for i, idx_name in enumerate(BROAD_INDICES):
    row = index_map.get(idx_name)
    if row:
        last = row.get("last", 0) or 0
        pct = row.get("percentChange", 0) or 0
        change = row.get("variation", 0) or 0
        cols[i].metric(idx_name.replace("NIFTY ", ""), f"{last:,.2f}",
                       f"{change:+.2f} ({pct:+.2f}%)")

st.divider()

# ---------- Sector heatmap ----------
st.subheader("🔥 Sector Performance — Today")

rows = []
for idx_name in SECTOR_INDICES:
    row = index_map.get(idx_name)
    if row:
        rows.append({
            "Sector": idx_name.replace("NIFTY ", ""),
            "Last": row.get("last", 0) or 0,
            "Change": row.get("variation", 0) or 0,
            "% Change": row.get("percentChange", 0) or 0,
            "Year High": row.get("yearHigh", 0) or 0,
            "Year Low": row.get("yearLow", 0) or 0,
        })

if not rows:
    st.warning("No sector data available right now.")
    st.stop()

df = pd.DataFrame(rows).sort_values("% Change", ascending=False).reset_index(drop=True)

# Color the % Change column
def color_pct(val):
    if val > 1.5:   return "background-color: #0a3d2e; color: #5dffac"
    if val > 0:     return "background-color: #1a3d2e; color: #8eff8e"
    if val < -1.5:  return "background-color: #4d1a1a; color: #ff7373"
    if val < 0:     return "background-color: #3d1f1f; color: #ffa3a3"
    return ""

styled = df.style.format({
    "Last": "{:,.2f}",
    "Change": "{:+,.2f}",
    "% Change": "{:+.2f}%",
    "Year High": "{:,.2f}",
    "Year Low": "{:,.2f}",
}).map(color_pct, subset=["% Change"])

st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ---------- Top gainers / losers ----------
top3 = df.head(3)
bot3 = df.tail(3).iloc[::-1]

c1, c2 = st.columns(2)
with c1:
    st.subheader("🚀 Top 3 Sectors")
    for _, r in top3.iterrows():
        st.metric(r["Sector"], f"{r['Last']:,.2f}", f"{r['% Change']:+.2f}%")
with c2:
    st.subheader("📉 Bottom 3 Sectors")
    for _, r in bot3.iterrows():
        st.metric(r["Sector"], f"{r['Last']:,.2f}", f"{r['% Change']:+.2f}%")

st.divider()
st.caption("📌 Data: NSE India • Cached 10 minutes • Sector tailwinds = consistent green over weeks")
