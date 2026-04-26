"""
Akram's Equity Research App — v0.1
Main entry point with authentication and welcome screen.
"""

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
st.caption("Personal stock & mutual fund research dashboard — built for the Indian markets")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Stock Analysis")
    st.markdown("""
    **GARP Framework** — long-term investing
    - 8-point pre-screen filter
    - Live price & fundamentals
    - Conviction score (1–10)
    
    Use the **Stock Analysis** page in the sidebar.
    """)

    st.subheader("💰 Mutual Fund Tracker")
    st.markdown("""
    **Live MF data via mfapi.in**
    - Search any Indian MF scheme
    - 1Y / 3Y / 5Y CAGR
    - Compare up to 3 funds
    
    Use the **MutuaC  
