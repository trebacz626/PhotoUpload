import streamlit as st
import requests
from api.client import get_base_url

BACKEND_URL = get_base_url()

auth_token = st.session_state.get("auth_token", None)

st.title("Upload Photo")

uploaded_file = st.file_uploader("Choose a photo to upload", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    if st.button("Upload"):
        files = {"image": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Token {auth_token}"

        try:
            API_UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/photos/upload_photo/"
            response = requests.post(API_UPLOAD_ENDPOINT, files=files, headers=headers)
            if response.status_code in (200, 201):
                st.success("Photo uploaded successfully!")
            else:
                st.error(f"Failed to upload: {response.status_code} {response.text}")
        except Exception as e:
            st.error(f"Error uploading file: {str(e)}")
