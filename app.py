import streamlit as st

st.set_page_config(
    page_title="Equity Research Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def check_password():
    def password_entered():
        try:
            correct_pw = st.secrets["app_password"]
        except (KeyError, FileNotFoundError):
            correct_pw = "akram2026"

        if st.session_state.get("password_input", "") == correct_pw:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("## 🔒 Equity Research Hub")
    st.markdown("Enter password to access the app.")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password_input"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Incorrect password. Try again.")
    return False


if not check_password():
    st.stop()


st.title("📊 Equity Research Hub")
st.caption("Personal stock & mutual fund research dashboard")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Stock Analysis")
    st.write("GARP Framework — long-term investing")
    st.write("- 8-point pre-screen filter")
    st.write("- Live price & fundamentals")
    st.write("- Conviction score (1–10)")
    st.write("Use the Stock Analysis page in the sidebar.")

    st.subheader("💰 Mutual Fund Tracker")
    st.write("Live MF data via mfapi.in")
    st.write("- Search any Indian MF scheme")
    st.write("- 1Y / 3Y / 5Y CAGR")
    st.write("- Compare up to 3 funds")
    st.write("Use the Mutual Funds page in the sidebar.")

with col2:
    st.subheader("⚡ Swing Trade Analysis")
    st.write("v2.0 Framework — short-term trades")
    st.write("- 4/6 pre-trade checklist")
    st.write("- Entry / SL / Target calculator")
    st.write("- Position sizing (₹2L, 2% risk)")
    st.write("Use the Swing Trade page in the sidebar.")

    st.subheader("🏭 Sector Heatmap")
    st.write("Nifty sectoral indices — live")
    st.write("- Today's % change")
    st.write("- 1M / 3M / 1Y returns")
    st.write("- Identify sector tailwinds")
    st.write("Use the Sector Heatmap page in the sidebar.")

st.markdown("---")

st.info("💡 Tip: Bookmark this URL on your phone for quick access. Share the URL + password with family.")

with st.sidebar:
    st.markdown("### 👤 Logged in")
    if st.button("Logout"):
        st.session_state["password_correct"] = False
        st.rerun()
