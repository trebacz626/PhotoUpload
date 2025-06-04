import streamlit as st
from api.client import get_photo_details, get_user_photos, get_current_user, delete_photo
from utils.session_state import get_session_state

state = get_session_state()

st.title("📸 My Uploaded Photos")


if "auth_token" not in st.session_state:
    st.warning("You must be logged in to view your photos.")
    st.stop()

token = st.session_state["auth_token"]  # <-- Define token here

user_info = get_current_user(token)

if not user_info or "pk" not in user_info:
    st.warning("You must be logged in to view your photos.")
    st.stop()

user_id = user_info["pk"]

try:
    photos = get_user_photos(user_id, token)
    if "error" in photos:
        st.error(f"Error loading photos: {photos['error']}")
    else:
        for photo in photos:
            photo_id = photo.get("photo_id") or photo.get("id")
            filename = photo.get("original_filename")
            uploaded = photo.get("upload_time")
            status = photo.get("processing_status")

            with st.expander(f"📄 {filename} — Status: {status}"):
                st.write(f"🆔 ID: {photo_id}")
                st.write(f"📅 Uploaded: {uploaded}")

                try:
                    details = get_photo_details(photo_id, token)
                    st.markdown("**📌 Photo Details:**")
                    st.json(details)
                except Exception as e:
                    st.error(f"Failed to load details: {e}")

                if st.button(f"🗑️ Delete Photo ID {photo_id}", key=f"delete_{photo_id}"):
                    result = delete_photo(photo_id, token)
                    if result["success"]:
                        st.success(f"Photo {photo_id} deleted successfully.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete photo: {result['status_code']} {result['error']}")

except Exception as e:
    st.error(f"Could not fetch photos: {e}")



