import requests
import os
import streamlit as st

def get_base_url():
    return os.getenv("BACKEND_API_URL", "https://landmark-app-api-jcj4dqmava-lm.a.run.app")

def login_user(username, password):
    base_url = get_base_url()
    return requests.post(
        f"{base_url}/api/v1/auth/login/",
        json={
            "username": username,
            "password": password,
        },
        headers={"Content-Type": "application/json"}  # explicit header
    )

def logout_user(token):
    base_url = get_base_url()
    url = f"{base_url}/api/v1/auth/logout/"
    headers = {"Authorization": f"Token {token}"}
    response = requests.post(url, headers=headers)
    if response.status_code in [200, 201]:
        return {"success": True}
    else:
        return {"success": False, "error": response.text}

def upload_photo(file_obj, filename, content_type, token=None):
    url = f"{get_base_url()}/api/photos/upload_photo/"
    headers = {}

    if token:
        headers["Authorization"] = f"Token {token}"

    files = {
        "image": (filename, file_obj, content_type)
    }

    response = requests.post(url, files=files, headers=headers)

    if response.status_code in (200, 201):
        return {"success": True, "response": response.json()}
    else:
        return {"success": False, "status_code": response.status_code, "error": response.text}

def delete_photo(photo_id, token):
    url = f"{get_base_url()}/api/v1/photos/{photo_id}/delete/"
    headers = {"Authorization": f"Token {token}"}

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        return {"success": True}
    else:
        return {"success": False, "status_code": response.status_code, "error": response.text}

def get_user_photos(user_id, token):
    base_url = get_base_url()
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{base_url}/api/v1/users/{user_id}/photos/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text, "status_code": response.status_code}

def get_current_user(token):
    base_url = get_base_url()
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{base_url}/api/v1/auth/user/", headers=headers)

    # Debugging output
    print("User info status:", response.status_code)
    print("User info response:", response.text)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_photo_details(photo_id, token):
    base_url = get_base_url()
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{base_url}/api/photos/{photo_id}/details/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_signed_url(photo_id, token):
    base_url = get_base_url()
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{base_url}/api/v1/photos/{photo_id}/signed_url/", headers=headers)

    if response.status_code == 200:
        return response.json().get("signed_url")
    else:
        # Add logging to help debug
        st.warning(f"Signed URL error: {response.status_code} — {response.text}")
        return None
    
