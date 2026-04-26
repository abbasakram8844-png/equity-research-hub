"""
Sector Heatmap — Nifty sectoral indices.
"""

import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Sector Heatmap", page_icon="🏭", layout="wide")

if not st.session_state.get("password_correct", False):
    st.error("Please log in from the main page first.")
    st.stop()

st.title("🏭 Sector Heatmap")
st.caption("Live performance of Nifty sectoral indices")

SECTORS = {
    "Nifty 50": "^NSEI",
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Energy": "^CNXENERGY",
    "Nifty Realty": "^CNXREALTY",
    "Nifty Financial Services": "^CNXFIN",
    "Nifty Infra": "^CNXINFRA",
    "Nifty PSU Bank": "^CNXPSUBANK",
    "Nifty Media": "^CNXMEDIA",
    "Nifty Smallcap 100": "^CNXSC",
    "Nifty Midcap 100": "^NSEMDCP50",
}


@st.cache_data(ttl=300)
def fetch_sector_data(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="1y")
        if hist.empty:
            return None
        latest = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) >= 2 else latest

        def pct_return(days):
            if len(hist) < days:
                return None
            return (latest / hist["Close"].iloc[-days] - 1) * 100

        return {
            "Latest": latest,
            "Day %": (latest / prev - 1) * 100 if prev else 0,
            "1W %": pct_return(5),
            "1M %": pct_return(21),
            "3M %": pct_return(63),
            "6M %": pct_return(126),
            "1Y %": pct_return(252),
        }
    except Exception:
        return None


with st.spinner("Fetching sectoral data..."):
    rows = []
    for name, ticker in SECTORS.items():
        data = fetch_sector_data(ticker)
        if data:
            rows.append({"Sector": name, **data})

if not rows:
    st.error("Couldn't fetch sector data.")
    st.stop()

df = pd.DataFrame(rows)

st.markdown("---")
st.subheader("📅 Today's Snapshot")

df_today = df.sort_values("Day %", ascending=False)
cols = st.columns(4)
for i, row in enumerate(df_today.head(8).itertuples()):
    with cols[i % 4]:
        st.metric(
            row.Sector.replace("Nifty ", ""),
            f"{row._2:,.0f}",
            f"{row._3:+.2f}%",
        )

st.markdown("---")
st.subheader("📊 Full Performance Table")

sort_by = st.selectbox(
    "Sort by",
    ["Day %", "1W %", "1M %", "3M %", "6M %", "1Y %"],
    index=3,
)
ascending = st.toggle("Ascending order", value=False)

df_sorted = df.sort_values(sort_by, ascending=ascending)
display_df = df_sorted.copy()
for col in ["Day %", "1W %", "1M %", "3M %", "6M %", "1Y %"]:
    display_df[col] = display_df[col].apply(
        lambda x: f"{x:+.2f}%" if pd.notnull(x) else "—"
    )
display_df["Latest"] = display_df["Latest"].apply(lambda x: f"{x:,.0f}")

st.dataframe(display_df, hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("🌬️ Tailwinds & Headwinds (3-month)")

col_t, col_h = st.columns(2)
top3 = df.sort_values("3M %", ascending=False).head(3)
bot3 = df.sort_values("3M %", ascending=True).head(3)

with col_t:
    st.markdown("**🟢 Top 3 Tailwinds**")
    for _, row in top3.iterrows():
        if pd.notnull(row["3M %"]):
            st.write(f"• **{row['Sector']}** — {row['3M %']:+.2f}%")

with col_h:
    st.markdown("**🔴 Top 3 Headwinds**")
    for _, row in bot3.iterrows():
        if pd.notnull(row["3M %"]):
            st.write(f"• **{row['Sector']}** — {row['3M %']:+.2f}%")
