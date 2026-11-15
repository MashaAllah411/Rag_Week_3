"""
ui/views/login_page.py

Modern, production-grade enterprise SaaS sign-in screen for DocChat Pro.
Designed to meet Linear/Stripe/Vercel visual standards with Inter typography,
ambient mesh gradient, glassmorphic elevation, technology badges,
and 1-click instant role-based access.
"""
import streamlit as st
from rag.auth_service import authenticate
from rag.feature_flags import get_active_flags


def render_login_page():
    # ── High-End SaaS Stylesheet ──────────────────────────────
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* ── Base Typography & Ambient Background ─────────────────── */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        .stApp {
            background: 
                radial-gradient(1100px circle at 50% -15%, rgba(59, 130, 246, 0.14), transparent 70%),
                radial-gradient(900px circle at 90% 85%, rgba(99, 102, 241, 0.09), transparent 60%),
                radial-gradient(700px circle at 10% 85%, rgba(14, 165, 233, 0.07), transparent 50%),
                var(--background-color, #f8fafc) !important;
            background-attachment: fixed !important;
            min-height: 100vh !important;
        }

        /* ── Center Layout Container ─────────────────────────────── */
        header[data-testid="stHeader"] { background: transparent !important; }
        
        .block-container {
            max-width: 470px !important;
            margin: 0 auto !important;
            padding-top: max(4.5vh, 28px) !important;
            padding-bottom: max(4.5vh, 28px) !important;
        }

        /* ── Enterprise Card Elevation ───────────────────────────── */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 20px !important;
            border: 1px solid rgba(226, 232, 240, 0.85) !important;
            background: var(--secondary-background-color, #ffffff) !important;
            box-shadow: 
                0 1px 3px 0 rgba(0, 0, 0, 0.03),
                0 12px 36px -4px rgba(15, 23, 42, 0.08),
                0 24px 60px -12px rgba(59, 130, 246, 0.07) !important;
            padding: 24px 28px 20px 28px !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
        }

        /* ── Header Elements ─────────────────────────────────────── */
        .auth-header {
            text-align: center;
            padding-bottom: 4px;
        }

        .auth-logo-badge {
            width: 52px;
            height: 52px;
            margin: 0 auto 12px auto;
            border-radius: 16px;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #4f46e5 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 22px -4px rgba(37, 99, 235, 0.4);
            transition: transform 0.25s ease;
        }
        .auth-logo-badge:hover {
            transform: scale(1.05) rotate(1deg);
        }

        .auth-title {
            font-size: 1.55rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #0f172a;
            margin: 0 0 4px 0;
            line-height: 1.2;
        }

        .auth-subtitle {
            font-size: 0.84rem;
            font-weight: 600;
            color: #4338ca;
            letter-spacing: -0.01em;
            margin-bottom: 6px;
        }

        .auth-tagline {
            font-size: 0.8rem;
            color: #64748b;
            line-height: 1.45;
            margin: 0 auto 14px auto;
            max-width: 380px;
        }

        /* ── Technology Badges ───────────────────────────────────── */
        .badge-container {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 20px;
        }

        .tech-badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 9px;
            border-radius: 9999px;
            background: rgba(241, 245, 249, 0.9);
            color: #334155;
            border: 1px solid rgba(226, 232, 240, 0.9);
            letter-spacing: 0.01em;
        }

        .badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
        }
        .dot-blue { background: #3b82f6; }
        .dot-indigo { background: #6366f1; }
        .dot-emerald { background: #10b981; }

        /* ── Input Styling ───────────────────────────────────────── */
        div[data-testid="stTextInput"] {
            margin-bottom: 10px !important;
        }

        div[data-testid="stTextInput"] label {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
            margin-bottom: 5px !important;
        }

        div[data-testid="stTextInput"] input {
            height: 42px !important;
            border-radius: 10px !important;
            border: 1px solid #cbd5e1 !important;
            padding: 0 14px !important;
            font-size: 0.92rem !important;
            background: #ffffff !important;
            color: #0f172a !important;
            transition: all 0.18s ease-in-out !important;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
            outline: none !important;
        }

        /* ── Submit Button ───────────────────────────────────────── */
        button[kind="primaryFormSubmit"] {
            height: 44px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 55%, #4f46e5 100%) !important;
            border: none !important;
            font-size: 0.94rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
            color: white !important;
            box-shadow: 0 4px 14px -1px rgba(37, 99, 235, 0.38) !important;
            transition: all 0.18s ease !important;
            margin-top: 6px !important;
        }

        button[kind="primaryFormSubmit"]:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px -2px rgba(37, 99, 235, 0.48) !important;
        }

        button[kind="primaryFormSubmit"]:active {
            transform: translateY(0px) !important;
        }

        /* ── Visual Section Divider ──────────────────────────────── */
        .auth-divider {
            display: flex;
            align-items: center;
            text-align: center;
            margin: 20px 0 14px 0;
            color: #94a3b8;
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.08em;
        }
        .auth-divider::before,
        .auth-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid rgba(226, 232, 240, 0.85);
        }
        .auth-divider::before { margin-right: 12px; }
        .auth-divider::after { margin-left: 12px; }

        /* ── Quick Demo Buttons ──────────────────────────────────── */
        .quick-access-btn button {
            height: 38px !important;
            border-radius: 9px !important;
            border: 1px solid #e2e8f0 !important;
            background: #f8fafc !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
            transition: all 0.15s ease !important;
        }

        .quick-access-btn button:hover {
            border-color: #93c5fd !important;
            background: #eff6ff !important;
            color: #1d4ed8 !important;
            transform: translateY(-1px) !important;
        }

        /* ── Security Footer ─────────────────────────────────────── */
        .auth-footer {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            font-size: 0.72rem;
            color: #94a3b8;
            margin-top: 18px;
            padding-top: 14px;
            border-top: 1px solid rgba(226, 232, 240, 0.75);
            font-weight: 500;
        }

        .footer-item {
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .footer-dot {
            color: #cbd5e1;
            font-size: 0.8rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── Main Login Card ───────────────────────────────────────
    with st.container(border=True):
        # Header
        st.markdown(
            """
            <div class="auth-header">
                <div class="auth-logo-badge">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <div class="auth-title">DocChat Pro</div>
                <div class="auth-subtitle">Enterprise Policy & Claims Intelligence</div>
                <div class="auth-tagline">
                    AI-powered semantic verification, instant claim triage, and compliance intelligence across enterprise manuals.
                </div>
                <div class="badge-container">
                    <span class="tech-badge"><span class="badge-dot dot-blue"></span>Groq LLM</span>
                    <span class="tech-badge"><span class="badge-dot dot-indigo"></span>Hybrid BM25 + RRF</span>
                    <span class="tech-badge"><span class="badge-dot dot-emerald"></span>AI Guardrails</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Credentials Form
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="e.g. demo or DataProp",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password",
            )
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            if submitted:
                with st.spinner("Authenticating credentials..."):
                    user_data = authenticate(username, password)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user_data
                        if "flags" not in st.session_state:
                            st.session_state["flags"] = get_active_flags()
                        st.rerun()
                    else:
                        st.error("Invalid username or password. Use quick access below for instant login.")

        # Quick Demo Access Divider
        st.markdown(
            """
            <div class="auth-divider">
                <span>OR INSTANT DEMO ACCESS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2 Equal-Width Quick Demo Access Buttons
        col_demo, col_admin = st.columns(2)
        with col_demo:
            st.markdown('<div class="quick-access-btn">', unsafe_allow_html=True)
            if st.button("👤 Demo User", use_container_width=True, help="Instant sign in as standard demo user"):
                with st.spinner("Signing in as Demo User..."):
                    user_data = authenticate("demo", "demo123")
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user_data
                        if "flags" not in st.session_state:
                            st.session_state["flags"] = get_active_flags()
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_admin:
            st.markdown('<div class="quick-access-btn">', unsafe_allow_html=True)
            if st.button("🛡️ Admin User", use_container_width=True, help="Instant sign in as DataProp admin"):
                with st.spinner("Signing in as Admin..."):
                    user_data = authenticate("DataProp", "admin2025")
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["user"] = user_data
                        if "flags" not in st.session_state:
                            st.session_state["flags"] = get_active_flags()
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Security & Compliance Footer
        st.markdown(
            """
            <div class="auth-footer">
                <span class="footer-item">Role-Based Access</span>
                <span class="footer-dot">•</span>
                <span class="footer-item">SHA-256 Auth</span>
                <span class="footer-dot">•</span>
                <span class="footer-item">Weeks 1–12 Capstone</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


render_login_page()
