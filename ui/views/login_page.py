"""
ui/views/login_page.py

Modern, production-grade sign-in screen with subtle ambient animation,
glassmorphic card elevation, feature badges, and one-click quick demo access.
"""
import streamlit as st
from rag.auth_service import authenticate
from rag.feature_flags import get_active_flags


def render_login_page():
    # Inject high-end styling and CSS animations
    st.markdown(
        """
        <style>
        /* ── Fullscreen Ambient Glow & Animated Mesh ─────────────── */
        .stApp {
            background: radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
                        radial-gradient(circle at 80% 80%, rgba(37, 99, 235, 0.08) 0%, transparent 45%),
                        radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%) !important;
            background-attachment: fixed !important;
        }

        /* Ambient floating orbs animation */
        @keyframes orbFloat {
            0% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-14px) scale(1.04); }
            100% { transform: translateY(0px) scale(1); }
        }

        @keyframes badgeShine {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* ── Container Layout ────────────────────────────────────── */
        header[data-testid="stHeader"] { background: transparent !important; }
        .block-container {
            max-width: 480px !important;
            padding-top: 5vh !important;
            padding-bottom: 4vh !important;
        }

        /* ── Glassmorphic Auth Card ──────────────────────────────── */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 24px !important;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            background: var(--secondary-background-color, rgba(255, 255, 255, 0.85)) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            box-shadow: 0 16px 40px -10px rgba(0, 0, 0, 0.12),
                        0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
            padding: 8px !important;
            animation: orbFloat 6s ease-in-out infinite !important;
        }

        /* ── Animated Brand Icon ─────────────────────────────────── */
        .brand-icon-wrap {
            width: 64px;
            height: 64px;
            margin: 4px auto 14px auto;
            border-radius: 20px;
            background: linear-gradient(135deg, #4f46e5 0%, #2563eb 50%, #06b6d4 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            box-shadow: 0 8px 24px -4px rgba(37, 99, 235, 0.45);
        }

        /* ── Input Styling ───────────────────────────────────────── */
        div[data-testid="stTextInput"] input {
            border-radius: 12px !important;
            padding: 11px 14px !important;
            font-size: 0.92rem !important;
            border: 1px solid rgba(128, 128, 128, 0.22) !important;
            background: var(--background-color, #ffffff) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #4f46e5 !important;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.18) !important;
        }

        /* ── Submit Button ───────────────────────────────────────── */
        button[kind="primaryFormSubmit"] {
            border-radius: 12px !important;
            padding: 11px 20px !important;
            font-weight: 600 !important;
            font-size: 0.94rem !important;
            margin-top: 6px !important;
            background: linear-gradient(135deg, #4f46e5 0%, #2563eb 100%) !important;
            border: none !important;
            box-shadow: 0 4px 14px -1px rgba(79, 70, 229, 0.4) !important;
            transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        }
        button[kind="primaryFormSubmit"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(79, 70, 229, 0.5) !important;
        }

        /* ── Quick Demo Pill Buttons ─────────────────────────────── */
        .quick-btn-wrap button {
            border-radius: 10px !important;
            font-size: 0.82rem !important;
            padding: 7px 12px !important;
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            background: rgba(128, 128, 128, 0.05) !important;
            transition: all 0.15s ease !important;
            font-weight: 500 !important;
        }
        .quick-btn-wrap button:hover {
            background: rgba(99, 102, 241, 0.12) !important;
            border-color: rgba(99, 102, 241, 0.4) !important;
            color: #4f46e5 !important;
            transform: translateY(-1px) !important;
        }

        /* ── Tech Badges ─────────────────────────────────────────── */
        .tech-pill {
            display: inline-block;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 20px;
            background: rgba(99, 102, 241, 0.09);
            color: #4f46e5;
            margin: 2px 3px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            letter-spacing: 0.02em;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        # ── Header with Glowing App Logo ───────────────────────────
        st.markdown(
            """
            <div style="text-align: center; padding: 12px 10px 4px 10px;">
                <div class="brand-icon-wrap">🤖</div>
                <div style="font-size: 1.65rem; font-weight: 800; letter-spacing: -0.03em;
                     background: linear-gradient(135deg, #1e293b 0%, #3b82f6 50%, #6366f1 100%);
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    DocChat Pro
                </div>
                <div style="color: #64748b; font-size: 0.86rem; margin-top: 4px; font-weight: 400;">
                    Enterprise Policy & Claims Intelligence Platform
                </div>
                <div style="margin: 14px 0 16px 0;">
                    <span class="tech-pill">⚡ Groq LLM</span>
                    <span class="tech-pill">🔍 Hybrid BM25+RRF</span>
                    <span class="tech-pill">🛡️ Guardrails</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Credentials Form ───────────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Enter username (e.g. demo or DataProp)",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="••••••••••••",
            )
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submitted:
                user_data = authenticate(username, password)
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    if "flags" not in st.session_state:
                        st.session_state["flags"] = get_active_flags()
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try the 1-click demo logins below.")

        # ── 1-Click Instant Demo Logins ────────────────────────────
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.76rem; text-transform: uppercase;
                 letter-spacing: 0.06em; color: #94a3b8; font-weight: 600; margin: 16px 0 8px 0;">
                Quick Demo Access
            </div>
            """,
            unsafe_allow_html=True,
        )

        q1, q2 = st.columns(2)
        with q1:
            st.markdown('<div class="quick-btn-wrap">', unsafe_allow_html=True)
            if st.button("🚀 Demo User", use_container_width=True, help="Login as standard demo user"):
                user_data = authenticate("demo", "demo123")
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    if "flags" not in st.session_state:
                        st.session_state["flags"] = get_active_flags()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with q2:
            st.markdown('<div class="quick-btn-wrap">', unsafe_allow_html=True)
            if st.button("🛡️ Admin (DataProp)", use_container_width=True, help="Login with full admin feature flags"):
                user_data = authenticate("DataProp", "admin2025")
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_data
                    if "flags" not in st.session_state:
                        st.session_state["flags"] = get_active_flags()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # ── Footer Info ────────────────────────────────────────────
        st.markdown(
            """
            <div style="text-align: center; font-size: 0.74rem; color: #94a3b8;
                 margin-top: 18px; border-top: 1px solid rgba(128,128,128,0.12);
                 padding-top: 12px; line-height: 1.4;">
                <span>🔒 Role-Based Access · SHA-256 Auth · Weeks 1-12 Capstone</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


render_login_page()
