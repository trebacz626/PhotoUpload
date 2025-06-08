import streamlit as st
from api.client import login_user
from utils.session_state import get_session_state
from components.navbar import show_navbar, show_sidebar
from utils.session_state import get_session_state

st.set_page_config(page_title="Login")
state = get_session_state()
show_navbar(state)
show_sidebar(state)
st.title("🔐 Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

    if submitted:
        res = login_user(username, password)
        if res.status_code == 200:
            token = res.json().get("key") 
            state['auth_token'] = token
            state['is_logged_in'] = True
            st.success("Logged in successfully!")
            st.switch_page("pages/gallery.py")
        else:
            st.error("Login failed. Please check your credentials.")


