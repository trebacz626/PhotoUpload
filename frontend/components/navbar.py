import streamlit as st
from api.client import logout_user

def show_navbar(state):
    nav_cols = st.columns([1, 1, 2, 1, 1])

    with nav_cols[0]:
        if st.button("🏠 Home"):
            st.switch_page("app.py")

    with nav_cols[1]:
        if state.get("is_logged_in"):
            if st.button("🖼️ My Gallery"):
                st.switch_page("pages/gallery.py")

    with nav_cols[3]:
        if not state.get("is_logged_in"):
            if st.button("🔐 Login"):
                st.switch_page("pages/login.py")

    with nav_cols[4]:
        if not state.get("is_logged_in"):
            if st.button("📝 Sign Up"):
                st.switch_page("pages/register.py")
        else:
            if st.button("🚪 Logout"):
                result = logout_user(state.get("auth_token"))
                if result.get("success"):
                    st.success("Logged out successfully.")
                    for key in list(state.keys()):
                        del state[key]
                    st.rerun()
                else:
                    st.error(f"Logout failed: {result.get('error')}")

def show_sidebar(state):
    st.sidebar.markdown("### Navigation")

    st.sidebar.page_link("app.py", label="🏠 Home")

    if state.get("is_logged_in"):
        st.sidebar.page_link("pages/gallery.py", label="🖼️ My Gallery")
