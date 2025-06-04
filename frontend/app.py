import streamlit as st
import requests
import os
from utils.session_state import get_session_state
from api.client import logout_user

# setting backend url
backend_url = os.environ.get("BACKEND_API_URL")

if not backend_url:
    st.error("Error: BACKEND_API_URL environment variable is not set.")
    st.stop()

if not backend_url.startswith(("http://", "https://")):
    backend_url = f"https://{backend_url}"

st.session_state["BACKEND_API_URL"] = backend_url

st.set_page_config(page_title="Photo Upload App", layout="wide")

state = get_session_state()

# logout
if state.get("is_logged_in"):
    with st.sidebar:
        if st.button("🚪 Log Out"):
            result = logout_user(state["auth_token"])
            if result.get("success"):
                st.success("Logged out successfully.")
                # Clear session
                for key in list(state.keys()):
                    del state[key]
                st.rerun()
            else:
                st.error(f"Logout failed: {result.get('error')}")



st.title("Photo Upload App - Database Status")
st.write("Use the sidebar to **login** or view your **uploaded photos**.")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page", ["Login", "Register", "Dashboard"])

if page == "Register":
    import pages.register
elif page == "Login":
    import pages.login

if state['is_logged_in']:
    st.success("✅ You are logged in.")
else:
    st.info("🔑 You are not logged in.")
