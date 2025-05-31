import streamlit as st
from api.client import login_user
from utils.session_state import get_session_state

st.title("🔐 Login")

state = get_session_state()

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

    if submitted:
        res = login_user(username, password)
        if res.status_code == 200:
            token = res.json().get("key")  # or 'access_token', check your API response
            state['auth_token'] = token
            state['is_logged_in'] = True
            st.success("Logged in successfully!")
        else:
            st.error("Login failed. Please check your credentials.")
            st.write(f"Status: {res.status_code}")
            st.write(f"Response: {res.text}")
