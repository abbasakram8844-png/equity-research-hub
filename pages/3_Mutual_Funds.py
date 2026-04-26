"""
Mutual Fund Tracker — uses mfapi.in
"""

import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Mutual Funds", page_icon="💰", layout="wide")

if not st.session_state.get("password_correct", False):
    st.error("Please log in from the main page first.")
    st.stop()

st.title("💰 Mutual Fund Tracker")
st.caption("Live data from mfapi.in — covers all Indian MF schemes")


@st.cache_data(ttl=3600)
def get_all_funds():
    try:
        r = requests.get("https://api.mfapi.in/mf", timeout=15)
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=900)
def get_fund_nav(scheme_code):
    try:
        r = requests.get(f"https://api.mfapi.in/mf/{scheme_code}", timeout=15)
        return r.json()
    except Exception:
        return None


def calc_cagr(nav_df, years):
    if nav_df.empty:
        return None
    end_date = nav_df.index.max()
    start_date = end_date - pd.DateOffset(years=years)
    past = nav_df[nav_df.index <= start_date]
    if past.empty:
        return None
    start_nav = past.iloc[-1]["nav"]
    end_nav = nav_df.iloc[-1]["nav"]
    if start_nav <= 0:
        return None
    return ((end_nav / start_nav) ** (1 / years) - 1) * 100


def parse_nav_history(data):
    if not data or "data" not in data:
        return pd.DataFrame()
    df = pd.DataFrame(data["data"])
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna().set_index("date").sort_index()
    return df


st.markdown("---")
search_term = st.text_input(
    "🔍 Search fund (e.g., 'Parag Parikh', 'HDFC Flexi Cap', 'SBI Small Cap')",
    value="",
).strip().lower()

if not search_term:
    st.info("👆 Type a fund name or AMC to search.")
    st.stop()

with st.spinner("Searching MF database..."):
    all_funds = get_all_funds()

if not all_funds:
    st.error("Couldn't fetch fund list. Try again in a moment.")
    st.stop()

matches = [f for f in all_funds if search_term in f["schemeName"].lower()][:50]

if not matches:
    st.warning(f"No funds found matching '{search_term}'.")
    st.stop()

st.success(f"Found {len(matches)} funds (showing top 50).")

fund_labels = [f"{f['schemeName']} (#{f['schemeCode']})" for f in matches]
selected = st.multiselect(
    "Select up to 3 funds to analyse/compare:",
    options=fund_labels,
    max_selections=3,
)

if not selected:
    st.info("👆 Pick 1–3 funds from the list above.")
    st.stop()

selected_codes = [int(s.split("#")[-1].rstrip(")")) for s in selected]

fund_results = []
with st.spinner("Loading NAV histories..."):
    for code in selected_codes:
        data = get_fund_nav(code)
        if data:
            nav_df = parse_nav_history(data)
            fund_results.append({
                "code": code,
                "name": data["meta"]["scheme_name"],
                "amc": data["meta"]["fund_house"],
                "category": data["meta"]["scheme_category"],
                "nav_df": nav_df,
            })

st.markdown("---")
st.subheader("📋 Fund Comparison")

summary_rows = []
for f in fund_results:
    nav_df = f["nav_df"]
    if nav_df.empty:
        continue
    latest_nav = nav_df.iloc[-1]["nav"]
    latest_date = nav_df.index.max().strftime("%d-%b-%Y")

    cagr_1y = calc_cagr(nav_df, 1)
    cagr_3y = calc_cagr(nav_df, 3)
    cagr_5y = calc_cagr(nav_df, 5)

    summary_rows.append({
        "Fund": f["name"][:60] + ("..." if len(f["name"]) > 60 else ""),
        "AMC": f["amc"],
        "Category": f["category"],
        "Latest NAV": f"₹{latest_nav:.2f}",
        "As of": latest_date,
        "1Y CAGR": f"{cagr_1y:.2f}%" if cagr_1y is not None else "—",
        "3Y CAGR": f"{cagr_3y:.2f}%" if cagr_3y is not None else "—",
        "5Y CAGR": f"{cagr_5y:.2f}%" if cagr_5y is not None else "—",
    })

if summary_rows:
    st.dataframe(pd.DataFrame(summary_rows), hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("📈 NAV History")

period = st.selectbox("Period", ["1Y", "3Y", "5Y", "All"], index=2)
years_map = {"1Y": 1, "3Y": 3, "5Y": 5, "All": 100}
years = years_map[period]

chart_data = pd.DataFrame()
for f in fund_results:
    nav_df = f["nav_df"]
    if nav_df.empty:
        continue
    cutoff = nav_df.index.max() - pd.DateOffset(years=years)
    sliced = nav_df[nav_df.index >= cutoff]
    if not sliced.empty:
        normalized = (sliced["nav"] / sliced["nav"].iloc[0]) * 100
        chart_data[f["name"][:40]] = normalized

if not chart_data.empty:
    st.line_chart(chart_data, height=400)
    st.caption("All NAVs normalised to 100 at start for comparison.")
