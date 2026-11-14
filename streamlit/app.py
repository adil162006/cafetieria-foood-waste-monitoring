import streamlit as st

from components.dashboard import render_conversation, render_dashboard

st.set_page_config(page_title="Cafeteria Food Waste Analytics", page_icon="🥗", layout="wide")
st.markdown("""
<style>
  .block-container {padding-top: 1.8rem;}
  [data-testid="stMetric"] {background: #f2f7f4; border: 1px solid #d9e8df; padding: 1rem; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)
st.sidebar.title("Food waste analytics")
page = st.sidebar.radio("Navigate", ["Dashboard", "Conversational analytics"])
st.sidebar.caption("Live metrics from the BigQuery dbt analytics layer")
if page == "Dashboard":
    render_dashboard()
else:
    render_conversation()
