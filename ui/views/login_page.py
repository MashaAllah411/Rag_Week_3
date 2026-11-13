"""
ui/views/login_page.py

Modern, centered sign-in card for user authentication.
Sets session state upon valid credentials and routes to the main workspace.
"""
import streamlit as st
from rag.auth_service import authenticate
from rag.feature_flags import get_active_flags


def render_login_page():
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 420px;
            margin: 60px auto 20px auto;
            padding: 32px;
            background: var(--secondary-background-color, #1e293b);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .login-title {
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            letter-spacing: -0.02em;
        }
        .login-subtitle {
            font-size: 0.9rem;
            color: #94a3b8;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        with st.container(border=True):
            st.markdown(
                """
                <div style="text-align: center; padding-top: 10px;">
                    <span style="font-size: 2.8rem;">🤖</span>
                    <h2 style="margin: 8px 0 4px 0; font-size: 1.6rem; font-weight: 700;">DocChat Pro</h2>
                    <p style="color: #64748b; font-size: 0.88rem; margin-bottom: 20px;">
                        Enterprise Document RAG & Policy Intelligence
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", placeholder="e.g. DataProp or demo")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submitted:
                    user_data = authenticate(username, password)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user_data
                        if "flags" not in st.session_state:
                            st.session_state["flags"] = get_active_flags()
                        st.success(f"Welcome back, {user_data['display_name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Check credentials and try again.")

            st.markdown(
                """
                <div style="text-align: center; font-size: 0.78rem; color: #64748b; margin-top: 15px; border-top: 1px solid rgba(128,128,128,0.2); padding-top: 10px;">
                    <span><b>Admin:</b> DataProp / admin2025</span> &nbsp;|&nbsp; <span><b>User:</b> demo / demo123</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


render_login_page()
