import streamlit as st
import os
from utils.session_state import get_session_state
# from api.client import logout_user
from components.navbar import show_navbar, show_sidebar

backend_url = os.environ.get("BACKEND_API_URL", "http://127.0.0.1:8000")
#backend_url = os.environ.get("BACKEND_API_URL")
if not backend_url:
    st.error("❌ BACKEND_API_URL environment variable is not set.")
    st.stop()
if not backend_url.startswith(("http://", "https://")):
    backend_url = f"https://{backend_url}"

st.session_state["BACKEND_API_URL"] = backend_url

st.set_page_config(page_title="Photo Upload App", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

state = get_session_state()

### Navigation ###
st.markdown("<h1 style='text-align: center;'>📸 Landmark Photo App</h1>", unsafe_allow_html=True)
show_navbar(state)
show_sidebar(state)

### Main page ###
st.divider()
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    st.subheader("👋 Welcome to the Landmark Photo App!")

    st.markdown("""
    Upload your photos and discover recognized landmarks from around the world!
    - 🌍 Automatic landmark detection  
    - 🗺️ View visited places on a global map  
    - 🖼️ Browse and manage your photo gallery  
    """)

    if not state.get("is_logged_in"):
        st.info("Please log in or register to start uploading photos.")
    else:
        st.success("You're logged in! Use the top navigation to access your gallery or upload new photos.")