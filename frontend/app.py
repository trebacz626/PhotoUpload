import streamlit as st
import requests
import os
from utils.session_state import get_session_state


backend_url = os.environ.get("BACKEND_API_URL")

if not backend_url:
    st.error("Error: BACKEND_API_URL environment variable is not set.")
    st.stop()

if not backend_url.startswith(("http://", "https://")):
    backend_url = f"https://{backend_url}"

st.session_state["BACKEND_API_URL"] = backend_url

st.set_page_config(page_title="Photo Upload App", layout="wide")

state = get_session_state()

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

### tests

# try:
#
#     response = requests.get(full_check_url, timeout=15)
#     response.raise_for_status()
#
#     st.success("Successfully connected to the backend API.")
#
#     try:
#         data = response.json()
#         st.subheader("Backend Response:")
#         st.json(data)
#
#         if data.get("status") == "ok":
#             st.success(f"Database Status: OK - {data.get('message', '')}")
#         else:
#             st.error(f"Database Status: Error- {data.get('message', '')}")
#
#     except requests.exceptions.JSONDecodeError:
#         st.error("Backend response was not valid JSON.")
#         st.text(response.text)
#
# except requests.exceptions.ConnectionError as e:
#     st.error(f"Connection Error: Could not connect to the backend API at {full_check_url}.")
#     st.error(f"Details: {e}")
# except requests.exceptions.Timeout:
#     st.error(f"Timeout Error")
# except requests.exceptions.RequestException as e:
#     st.error(f"Request Error: An error occurred while contacting the backend API.")
#     st.error(f"Details: {e}")
#     if e.response is not None:
#         st.error(f"Status Code: {e.response.status_code}")
#         st.text(f"Response Text: {e.response.text}")
#
# st.button("Re-check Status")