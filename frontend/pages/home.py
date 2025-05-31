import streamlit as st
from api.client import get_user_photos
from utils.session_state import get_session_state

st.title("📸 Your Uploaded Photos")

state = get_session_state()

if not state['is_logged_in']:
    st.warning("Please login first via the sidebar.")
else:
    photos = get_user_photos(state['auth_token'])
    if photos:
        for photo in photos:
            st.image(photo['image_url'], caption=photo.get("title", "Uploaded photo"))
    else:
        st.info("No photos found.")
