import streamlit as st
from api.client import get_base_url, login_user
import requests

BACKEND_URL = get_base_url()

st.title("Register")

username = st.text_input("Username")
email = st.text_input("Email")
password1 = st.text_input("Password", type="password")
password2 = st.text_input("Confirm Password", type="password")

if st.button("Register"):
    if password1 != password2:
        st.error("Passwords do not match.")
    elif not username or not email or not password1:
        st.error("Please fill out all fields.")
    else:
        data = {
            "username": username,
            "email": email,
            "password1": password1,
            "password2": password2
        }

        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/auth/registration/",
                json=data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 201:
                st.success("Registration successful!")

                # Use the shared login_user function
                login_response = login_user(username, password1)

                if login_response.status_code == 200:
                    token = login_response.json().get("key")
                    if token:
                        st.session_state["auth_token"] = token
                        st.session_state["username"] = username
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.warning("Login successful but no token received.")
                else:
                    st.error("Registration succeeded, but login failed.")
                    st.error(login_response.text)

            else:
                try:
                    st.error(f"Error: {response.json()}")
                except Exception:
                    st.error(f"Unexpected server response:\n{response.text}")

        except Exception as e:
            st.error(f"Failed to register: {str(e)}")
