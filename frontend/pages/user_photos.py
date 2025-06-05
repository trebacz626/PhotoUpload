import streamlit as st
from api.client import get_user_photos, get_current_user, get_photo_details, get_signed_url

st.title("My Uploaded Photos")

# Ensure user is logged in
if "auth_token" not in st.session_state:
    st.warning("You must be logged in to view your photos.")
    st.stop()

token = st.session_state["auth_token"]  # <-- Define token here

user_info = get_current_user(token)

if not user_info or "pk" not in user_info:
    st.warning("You must be logged in to view your photos.")
    st.stop()

user_id = user_info["pk"]

photos = get_user_photos(user_id, token)

if "error" in photos:
    st.error(f"Error loading photos: {photos['error']}")
else:
    st.header("📸 My Uploaded Photos")
    for photo in photos:
        photo_id = photo.get("photo_id") or photo.get("id")
        filename = photo.get("original_filename")
        uploaded = photo.get("upload_time")
        status = photo.get("processing_status")

        st.markdown(f"### 📂 {filename}")
        st.markdown(f"🕒 Uploaded: {uploaded}")
        st.markdown(f"⚙️ Status: {status}")

        if photo_id:
            signed_url = get_signed_url(photo_id, token)
            st.markdown(signed_url)
            if signed_url:
                st.image(signed_url, caption=filename, use_container_width=True)
            else:
                st.warning("🔒 Could not generate signed URL.")
        else:
            st.warning("Photo ID missing, cannot show image.")

        details = get_photo_details(photo_id, token) if photo_id else None
        if details and details.get("landmark_data"):
            landmark = details["landmark_data"]
            st.markdown(f"🏛️ **Detected Landmark:** {landmark.get('detected_landmark_name')}")
            st.markdown(f"📍 **Location:** {landmark.get('formatted_address')}")
        st.divider()
