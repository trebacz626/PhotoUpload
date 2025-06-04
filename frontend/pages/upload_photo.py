import streamlit as st
from api.client import upload_photo

auth_token = st.session_state.get("auth_token", None)

st.title("📤 Upload Photo")

uploaded_file = st.file_uploader("Choose a photo to upload", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    if st.button("Upload"):
        result = upload_photo(
            file_obj=uploaded_file,
            filename=uploaded_file.name,
            content_type=uploaded_file.type,
            token=auth_token
        )

        if result["success"]:
            st.success("Photo uploaded successfully!")
        else:
            st.error(f"Failed to upload: {result['status_code']} {result['error']}")


# import streamlit as st
# import requests
# from api.client import get_base_url, upload_photo
#
# # logic should be moved to client.py
# BACKEND_URL = get_base_url()
#
# auth_token = st.session_state.get("auth_token", None)
#
# st.title("Upload Photo")
#
# uploaded_file = st.file_uploader("Choose a photo to upload", type=["jpg", "jpeg", "png"])
#
# if uploaded_file is not None:
#     if st.button("Upload"):
#         files = {"image": (uploaded_file.name, uploaded_file, uploaded_file.type)}
#
#         headers = {}
#         if auth_token:
#             headers["Authorization"] = f"Token {auth_token}"
#
#         try:
#             API_UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/photos/upload_photo/"
#             response = requests.post(API_UPLOAD_ENDPOINT, files=files, headers=headers)
#             if response.status_code in (200, 201):
#                 st.success("Photo uploaded successfully!")
#             else:
#                 st.error(f"Failed to upload: {response.status_code} {response.text}")
#         except Exception as e:
#             st.error(f"Error uploading file: {str(e)}")
