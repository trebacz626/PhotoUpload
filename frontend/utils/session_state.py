import streamlit as st

@st.cache_resource
def get_session_state():
    # if 'auth_token' not in st.session_state:
    #     st.session_state['auth_token'] = None
    #     st.session_state['is_logged_in'] = False
    # return st.session_state
    return {"auth_token": None, "is_logged_in": False}
