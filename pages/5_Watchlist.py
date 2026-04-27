@st.cache_data(ttl=600, show_spinner=False)
def fetch_quote(symbol: str):
    """Try main equity, then SME with proper referer."""
    sym = symbol.upper().strip()
    
    # Try 1: Main equity (uses default session referer)
    s = get_nse_session()
    try:
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            if (data.get("priceInfo", {}) or {}).get("lastPrice"):
                return data, "EQ"
    except Exception:
        pass
    time.sleep(0.3)
    
    # Try 2: SME endpoint with SME-specific referer
    sme_headers = NSE_HEADERS.copy()
    sme_headers["Referer"] = f"https://www.nseindia.com/get-quotes/sme?symbol={sym}"
    try:
        # Warm up SME page first
        s.get(f"https://www.nseindia.com/get-quotes/sme?symbol={sym}",
              headers=sme_headers, timeout=10)
        time.sleep(0.3)
        r = s.get(f"https://www.nseindia.com/api/quote-equity?symbol={sym}",
                  headers=sme_headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if (data.get("priceInfo", {}) or {}).get("lastPrice"):
                return data, "SME"
    except Exception:
        pass
    
    return None, None
