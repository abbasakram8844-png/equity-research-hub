import streamlit as st
import requests
import time

st.set_page_config(page_title="Stock Analysis", page_icon="📈", layout="wide")

st.title("📈 Stock Analysis — GARP Framework")
st.caption("Live NSE snapshot → Screener deep-dive → 8-point pre-screen")

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
def fetch_nse(symbol: str):
    s = get_nse_session()
    sym = symbol.upper().strip()
    quote, trade = None, None
    for attempt in range(2):
        try:
            r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=12)
            if r.status_code == 200:
                quote = r.json()
                break
        except Exception:
            time.sleep(1)
    try:
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}&section=trade_info", timeout=12)
        if r.status_code == 200:
            trade = r.json()
    except Exception:
        pass
    return quote, trade

# ---------- Input ----------
col1, col2 = st.columns([3, 1])
with col1:
    symbol = st.text_input("NSE Symbol (no suffix)", value="RELIANCE",
                           help="Examples: RELIANCE, BLS, AVANTEL, TCS, NEETUYO")
with col2:
    st.write("")
    st.write("")
    go = st.button("🔍 Analyze", type="primary", use_container_width=True)

if not go:
    st.info("Enter an NSE symbol and click Analyze.")
    st.stop()

with st.spinner(f"Fetching {symbol} from NSE India…"):
    quote, trade = fetch_nse(symbol)

if quote is None:
    st.error(
        "⚠️ Could not fetch from NSE.\n\n"
        "**Possible reasons:**\n"
        "- Symbol is misspelled (try without `.NS` suffix)\n"
        "- Stock is on BSE only (NSE API won't have it)\n"
        "- NSE rate-limited the session — wait 30 seconds and retry"
    )
    st.stop()

# ---------- Extract ----------
info = quote.get("info", {}) or {}
price = quote.get("priceInfo", {}) or {}
meta = quote.get("metadata", {}) or {}
industry_info = quote.get("industryInfo", {}) or {}

company = info.get("companyName", symbol)
isin = info.get("isin", "—")
last = price.get("lastPrice", 0) or 0
change = price.get("change", 0) or 0
pct = price.get("pChange", 0) or 0
prev_close = price.get("previousClose", 0) or 0
open_p = price.get("open", 0) or 0
intra = price.get("intraDayHighLow", {}) or {}
yhl = price.get("weekHighLow", {}) or {}
day_high = intra.get("max", 0) or 0
day_low = intra.get("min", 0) or 0
y_high = yhl.get("max", 0) or 0
y_low = yhl.get("min", 0) or 0

sector_macro = industry_info.get("macro", "—")
sector = industry_info.get("sector", "—")
industry = industry_info.get("industry", "—")
basic_industry = industry_info.get("basicIndustry", "—")
listing_date = meta.get("listingDate", "—")
sector_pe = meta.get("pdSectorPe", None)

# Market cap (in crores) from trade_info
mcap_full = 0
mcap_free = 0
if trade:
    tinfo = (trade.get("marketDeptOrderBook", {}) or {}).get("tradeInfo", {}) or {}
    mcap_full = tinfo.get("totalMarketCap", 0) or 0
    mcap_free = tinfo.get("ffmc", 0) or 0

# ---------- Header ----------
st.success(f"✅ **{company}** ({symbol.upper()}) • {basic_industry}")

# ---------- Top metrics ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Price (₹)", f"{last:,.2f}", f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("Day Range", f"₹{day_low:,.2f} – {day_high:,.2f}")
c3.metric("52W High", f"₹{y_high:,.2f}")
c4.metric("52W Low", f"₹{y_low:,.2f}")

# Distance from 52W high (useful GARP signal)
if y_high:
    pct_from_high = ((last - y_high) / y_high) * 100
    pct_from_low = ((last - y_low) / y_low) * 100 if y_low else 0
    c1, c2 = st.columns(2)
    c1.metric("From 52W High", f"{pct_from_high:+.1f}%")
    c2.metric("From 52W Low", f"{pct_from_low:+.1f}%")

st.divider()

# ---------- Market cap & classification ----------
st.subheader("🏢 Company Snapshot")
c1, c2, c3 = st.columns(3)
if mcap_full:
    c1.metric("Market Cap", f"₹{mcap_full:,.0f} Cr")
    cap_class = ("Large Cap" if mcap_full > 20000
                 else "Mid Cap" if mcap_full > 5000
                 else "Small Cap")
    c2.metric("Cap Classification", cap_class)
else:
    c1.metric("Market Cap", "—")
    c2.metric("Cap Classification", "—")
c3.metric("Listed Since", listing_date)

c1, c2, c3 = st.columns(3)
c1.metric("Macro Sector", sector_macro)
c2.metric("Sector", sector)
c3.metric("Industry", industry)

if sector_pe:
    st.metric("Sector P/E", f"{sector_pe}")

st.divider()

# ---------- Screener deep-dive ----------
st.subheader("📊 Full Fundamentals — 8-Point Pre-Screen")
st.markdown(
    "NSE doesn't expose ROCE / ROE 3Y / D/E / OCF / FII+DII / PEG. "
    "Open this stock on Screener.in to run your full pre-screen:"
)
sc1, sc2 = st.columns(2)
sc1.link_button(
    f"🔗 Open {symbol.upper()} on Screener (Consolidated)",
    f"https://www.screener.in/company/{symbol.upper()}/consolidated/",
    use_container_width=True,
)
sc2.link_button(
    f"🔗 Open {symbol.upper()} on Screener (Standalone)",
    f"https://www.screener.in/company/{symbol.upper()}/",
    use_container_width=True,
)

st.markdown("**Your 8-point pre-screen criteria:**")
st.markdown("""
- ROCE ≥ 20%
- ROE 3Y ≥ 15%
- Revenue CAGR 3Y ≥ 15%
- Promoter > 50% & Pledge = 0%
- D/E ≤ 0.5×
- OCF positive 2 of 3 years
- FII + DII ≥ 1%
- PEG ≤ 0.5
""")

st.info("💡 **Phase 2 coming:** Manual entry of the 8 metrics → automatic conviction score (1–10) computed in-app.")

st.divider()

# ---------- Quick links ----------
st.subheader("🔗 Quick Links")
ql1, ql2, ql3 = st.columns(3)
ql1.link_button("📈 NSE Live Quote",
                f"https://www.nseindia.com/get-quotes/equity?symbol={symbol.upper()}",
                use_container_width=True)
ql2.link_button("📊 Tickertape",
                f"https://www.tickertape.in/stocks/{symbol.lower()}",
                use_container_width=True)
ql3.link_button("🏛️ BSE",
                f"https://www.bseindia.com/stock-share-price/{symbol.lower()}/",
                use_container_width=True)

st.caption(f"📌 Data: NSE India • ISIN: `{isin}` • Cached 10 minutes")
