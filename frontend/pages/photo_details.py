import streamlit as st
from api.client import get_photo_details, get_signed_url, get_current_user, delete_photo
from utils.session_state import get_session_state
from components.navbar import show_navbar, show_sidebar


state = get_session_state()

show_navbar(state)
show_sidebar(state)
st.title("📷 Photo Details")

if not state.get("is_logged_in") or "auth_token" not in state:
    st.warning("You must be logged in to view photo details.")
    st.stop()

token = state["auth_token"]

photo_id = st.query_params.get("photo_id", [None])[0]
print(st.query_params)

if not photo_id:
    st.error("No photo ID specified.")
    st.stop()

user_info = get_current_user(token)
if not user_info or "pk" not in user_info:
    st.warning("Invalid session or not logged in.")
    st.stop()

try:
    details = get_photo_details(photo_id, token)
    if not details:
        st.error("Failed to load photo details.")
        st.stop()

    signed_url = get_signed_url(photo_id, token)

    if signed_url:
        col1, col2, col3 = st.columns([1, 3, 1]) 
        with col2:
            st.image(signed_url, use_container_width=True)
    else:
        st.warning("Could not load photo image.")

    st.markdown("### 🗂️ Photo Info")
    st.markdown(f"**Filename:** {details.get('original_filename', 'N/A')}")
    st.markdown(f"**Uploaded:** {details.get('upload_time', 'N/A')}")
    st.markdown(f"**Status:** {details.get('processing_status', 'N/A')}")

    if details.get("landmark_data"):
        landmark = details["landmark_data"]
        st.markdown("### 🏛️ Landmark Data")
        st.markdown(f"**Detected Landmark:** {landmark.get('detected_landmark_name', 'N/A')}")
        st.markdown(f"**Location:** {landmark.get('formatted_address', 'N/A')}")
        coords = landmark.get('coordinates')
        if coords:
            st.markdown(f"**Coordinates:** {coords}")

    if st.button("🗑️ Delete Photo"):
        result = delete_photo(photo_id, token)
        if result.get("success"):
            st.success("Photo deleted successfully.")
            st.switch_page("pages/gallery.py")
        else:
            st.error(f"Failed to delete photo: {result.get('error', 'Unknown error')}")

except Exception as e:
    st.error(f"An error occurred: {e}")

if st.button("🔙 Back to My Gallery"):
    st.query_params = {}
    st.switch_page("pages/gallery.py")



