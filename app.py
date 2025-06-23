import streamlit as st
import threading
from main import main_loop

# Стримлит ничего не показывает
st.set_page_config(page_title="AI Email Bot", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)
st.markdown("<!-- hidden bot -->", unsafe_allow_html=True)

# Запускаем фон
if "thread_started" not in st.session_state:
    st.session_state.thread_started = True
    threading.Thread(target=main_loop, daemon=True).start()
    st.write("✅ Background bot running...")
