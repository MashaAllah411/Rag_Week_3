"""
ui/views/login_page.py

Modern, production-grade enterprise SaaS sign-in screen for DocChat Pro.
Features a spacious two-column split layout on desktop to effectively utilize widescreen real estate,
highlighting platform capabilities on the left and the interactive auth card on the right.
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
                radial-gradient(1200px circle at 20% -10%, rgba(59, 130, 246, 0.12), transparent 70%),
                radial-gradient(1000px circle at 90% 85%, rgba(99, 102, 241, 0.10), transparent 60%),
                radial-gradient(800px circle at 50% 50%, rgba(14, 165, 233, 0.05), transparent 50%),
                var(--background-color, #f8fafc) !important;
            background-attachment: fixed !important;
            min-height: 100vh !important;
        }

        /* ── Center Layout Container (Spacious 1060px) ───────────── */
        header[data-testid="stHeader"] { background: transparent !important; }
        
        .block-container {
            max-width: 1080px !important;
            margin: 0 auto !important;
            padding-top: max(5vh, 32px) !important;
            padding-bottom: max(5vh, 32px) !important;
        }

        /* ── Left Showcase Styling ───────────────────────────────── */
        .showcase-container {
            padding: 12px 24px 12px 0;
        }

        .showcase-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #4338ca;
            background: rgba(99, 102, 241, 0.1);
            padding: 5px 13px;
            border-radius: 9999px;
            border: 1px solid rgba(99, 102, 241, 0.22);
            margin-bottom: 16px;
        }

        .pill-pulse {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
        }

        .showcase-heading {
            font-size: 2.15rem;
            font-weight: 800;
            line-height: 1.22;
            letter-spacing: -0.035em;
            color: #0f172a;
            margin-bottom: 14px;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 65%, #4338ca 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .showcase-lead {
            font-size: 0.94rem;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 22px;
        }

        .feature-card {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px 14px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(226, 232, 240, 0.85);
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease;
        }
        .feature-card:hover {
            background: #ffffff;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
            transform: translateX(4px);
            border-color: rgba(99, 102, 241, 0.3);
        }

        .feature-icon {
            font-size: 1.25rem;
            line-height: 1;
            padding-top: 2px;
        }

        .feature-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 2px;
        }

        .feature-desc {
            font-size: 0.78rem;
            color: #64748b;
            line-height: 1.4;
        }

        .stats-row {
            display: flex;
            gap: 16px;
            margin-top: 22px;
            padding-top: 18px;
            border-top: 1px solid rgba(226, 232, 240, 0.85);
        }

        .stat-box {
            flex: 1;
        }

        .stat-value {
            font-size: 1.35rem;
            font-weight: 800;
            color: #1e40af;
            letter-spacing: -0.02em;
        }

        .stat-label {
            font-size: 0.72rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-top: 2px;
        }

        /* ── Right Card Elevation ────────────────────────────────── */
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

        /* ── Header Elements inside Card ─────────────────────────── */
        .auth-header {
            text-align: center;
            padding-bottom: 4px;
        }

        .auth-logo-badge {
            width: 48px;
            height: 48px;
            margin: 0 auto 10px auto;
            border-radius: 14px;
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #4f46e5 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 20px -3px rgba(37, 99, 235, 0.4);
        }

        .auth-title {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            color: #0f172a;
            margin: 0 0 4px 0;
            line-height: 1.2;
        }

        .auth-subtitle {
            font-size: 0.82rem;
            font-weight: 600;
            color: #4338ca;
            letter-spacing: -0.01em;
            margin-bottom: 12px;
        }

        /* ── Technology Badges ───────────────────────────────────── */
        .badge-container {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 18px;
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
            margin-bottom: 8px !important;
        }

        div[data-testid="stTextInput"] label {
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #334155 !important;
            margin-bottom: 4px !important;
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
            margin: 18px 0 12px 0;
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
            margin-top: 16px;
            padding-top: 12px;
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

    # ── Two-Column Split Layout for Desktop / Widescreen ───────
    col_showcase, col_auth = st.columns([1.18, 1], gap="large")

    with col_showcase:
        st.markdown(
            """
            <div class="showcase-container">
                <div class="showcase-pill">
                    <span class="pill-pulse"></span> Production Capstone (Weeks 1–12)
                </div>
                <h1 class="showcase-heading">
                    Enterprise Policy Intelligence & Automated Claims Verification
                </h1>
                <p class="showcase-lead">
                    Unified conversational RAG architecture querying complex policy manuals,
                    clauses, and exclusions with sub-2s latency and verifiable chunk citations.
                </p>

                <div class="feature-card">
                    <div class="feature-icon">⚡</div>
                    <div>
                        <div class="feature-title">Ultra-Fast Groq Inference</div>
                        <div class="feature-desc">~1.5s real-time synthesis via Groq cloud LLM with local Ollama fallback.</div>
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <div>
                        <div class="feature-title">Hybrid BM25 + Vector Search</div>
                        <div class="feature-desc">Reciprocal Rank Fusion (RRF) across ChromaDB dense vectors and keyword indices.</div>
                    </div>
                </div>

                <div class="feature-card">
                    <div class="feature-icon">🛡️</div>
                    <div>
                        <div class="feature-title">Enterprise AI Guardrails</div>
                        <div class="feature-desc">Active prompt-injection quarantine, safety triage, and strict hallucination rejection.</div>
                    </div>
                </div>

                <div class="stats-row">
                    <div class="stat-box">
                        <div class="stat-value">167+</div>
                        <div class="stat-label">Indexed Chunks</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">~1.5s</div>
                        <div class="stat-label">Groq Latency</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">64/64</div>
                        <div class="stat-label">Tests Passed</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_auth:
        with st.container(border=True):
            # Header
            st.markdown(
                """
                <div class="auth-header">
                    <div class="auth-logo-badge">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                        </svg>
                    </div>
                    <div class="auth-title">DocChat Pro</div>
                    <div class="auth-subtitle">Sign in to your enterprise workspace</div>
                    <div class="badge-container">
                        <span class="tech-badge"><span class="badge-dot dot-blue"></span>Groq LLM</span>
                        <span class="tech-badge"><span class="badge-dot dot-indigo"></span>Hybrid BM25</span>
                        <span class="tech-badge"><span class="badge-dot dot-emerald"></span>Guardrails</span>
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
                            st.error("Invalid credentials. Use 1-click access below.")

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
                    <span class="footer-item">Cap. W1-12</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


render_login_page()
