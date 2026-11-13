"""
ui/views/login_page.py

Modern, centered sign-in card for user authentication.
Sets session state upon valid credentials and routes to the main workspace.
"""
import streamlit as st
from rag.auth_service import authenticate
from rag.feature_flags import get_active_flags


def render_login_page():
    # Full-page centered layout with professional styling
    st.markdown(
        """
        <style>
        /* Hide header and footer on login */
        header[data-testid="stHeader"] { background: transparent !important; }
        .block-container {
            max-width: 480px !important;
            padding-top: 8vh !important;
        }

        /* Login card styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px !important;
            border: 1px solid rgba(128, 128, 128, 0.12) !important;
            box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.08) !important;
        }

        /* Form inputs */
        div[data-testid="stTextInput"] input {
            border-radius: 10px !important;
            padding: 10px 14px !important;
            font-size: 0.9rem !important;
        }

        /* Sign in button */
        button[kind="primaryFormSubmit"] {
            border-radius: 10px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            font-size: 0.92rem !important;
            margin-top: 4px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            """
            <div style="text-align: center; padding: 16px 0 8px 0;">
                <div style="font-size: 2.4rem; margin-bottom: 8px;">🤖</div>
                <div style="font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em;">
                    DocChat Pro
                </div>
                <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 4px; margin-bottom: 20px;">
                    Enterprise Document RAG & Policy Intelligence
                </div>
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
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        st.markdown(
            """
            <div style="text-align: center; font-size: 0.75rem; color: #94a3b8;
                 margin-top: 12px; border-top: 1px solid rgba(128,128,128,0.12);
                 padding-top: 12px;">
                <strong>Admin:</strong> DataProp / admin2025 &nbsp;·&nbsp;
                <strong>User:</strong> demo / demo123
            </div>
            """,
            unsafe_allow_html=True,
        )


render_login_page()
