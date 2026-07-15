"""
login.py
�??�??�??�??�??�??�??�??
Simple login gate for AskBVRITH.

When ENABLE_LOGIN=true in .env, users must enter credentials before
accessing the chatbot. Credentials are read from LOGIN_USERNAME and
LOGIN_PASSWORD env vars (default: admin / bvrit2024).

check_login() returns True when the user is authenticated (or when login
is disabled), and False otherwise — in which case the caller should st.stop().
"""

import os
import hashlib

import streamlit as st


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def check_login() -> bool:
    """Return True if the user is authenticated."""
    expected_user = os.getenv("LOGIN_USERNAME", "admin")
    expected_pass = os.getenv("LOGIN_PASSWORD", "bvrit2024")

    # Already logged in this session
    if st.session_state.get("authenticated"):
        return True

    st.markdown(
        """
        <style>
        .login-box {
            max-width: 380px;
            margin: 6rem auto 0;
            background: #fff;
            border: 1px solid #D8E4C8;
            border-radius: 18px;
            padding: 2rem 2.2rem;
            box-shadow: 0 12px 36px rgba(46,94,46,0.10);
        }
        .login-title {
            font-size: 1.4rem;
            font-weight: 700;
            color: #1B5E20;
            margin-bottom: 0.2rem;
            text-align: center;
        }
        .login-sub {
            font-size: 0.82rem;
            color: #5A7748;
            text-align: center;
            margin-bottom: 1.4rem;
        }
        </style>
        <div class="login-box">
          <p class="login-title">🎓 AskBVRITH</p>
          <p class="login-sub">Sign in to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if username == expected_user and password == expected_pass:
            st.session_state["authenticated"] = True
            st.session_state["login_username"] = username
            st.rerun()
        else:
            st.error("Invalid username or password.")

    return False


