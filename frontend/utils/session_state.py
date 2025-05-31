import streamlit as st

def get_session_state():
    if 'auth_token' not in st.session_state:
        st.session_state['auth_token'] = None
        st.session_state['is_logged_in'] = False
    return st.session_state
