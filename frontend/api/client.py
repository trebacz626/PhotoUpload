import requests
import os

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

def get_user_photos(token):
    base_url = get_base_url()
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(f"{base_url}/users/1/photos/", headers=headers)  # user_id is 1 for demo
    if response.status_code == 200:
        return response.json()
    return []
