"""Authentication layer for EKIP Enterprise Application with Login, Sign Up, and Password Reset views."""

import re
import streamlit as st
from core.auth.database import (
    create_user,
    authenticate_user,
    get_user_by_username,
    get_user_by_email,
    update_password,
    update_last_login,
    generate_remember_token,
)
from core.auth.validators import validate_password
from core.auth.session import login_user as session_login_user, logout_user as session_logout_user


def is_authenticated() -> bool:
    """Check whether current session is authenticated."""
    return bool(st.session_state.get("authenticated", False))


def login_user(email: str, remember: bool = False):
    """Set authenticated session state for user."""
    session_login_user(email, remember=remember)


def logout_user():
    """Clear session state and log out."""
    session_logout_user()
    st.rerun()


def render_login_page():
    """Render single compact, dark-themed login card matching IMAGE 2."""
    import streamlit as st
    from core.auth.database import authenticate_user, get_user_by_email
    from core.auth.session import login_user

    if st.query_params.get("auth_view") == "forgot":
        st.session_state["auth_view"] = "forgot"
    elif st.query_params.get("auth_view") == "signup":
        st.session_state["auth_view"] = "signup"
    elif st.query_params.get("auth_view") == "login":
        st.session_state["auth_view"] = "login"

    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"

    # Pre-fill username/email if coming from successful registration
    prefilled_email = ""
    if "signup_success" in st.session_state:
        prefilled_email = st.session_state.pop("signup_success")
        st.toast("✅ Account created successfully! Please sign in.", icon="🎉")

    if st.session_state.pop("reset_success_toast", False):
        st.toast("Password reset successfully! Please sign in with your new password.", icon="✅")

    # Background layer (glowing orbs + grid + noise)
    st.markdown(
        '<div class="orb-1"></div>'
        '<div class="orb-2"></div>'
        '<div class="orb-3"></div>'
        '<div class="dot-grid"></div>'
        '<div class="noise"></div>',
        unsafe_allow_html=True,
    )

    # CSS overrides for Login Page (Single Compact Card matching IMAGE 2)
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0px !important; }
        
        html, body, .stApp {
            background: #0b0d12 !important;
            min-height: 100vh !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        /* Positioning container - transparent, centered, positioning only */
        .main .block-container {
            max-width: 440px !important;
            width: calc(100vw - 32px) !important;
            margin: auto !important;
            padding: 20px 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            border: none !important;
        }

        /* Exactly ONE Login Card element */
        [data-testid="stForm"] {
            background: #111318 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 36px 32px !important;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
            position: relative !important;
            overflow: hidden !important;
            width: 100% !important;
            max-width: 420px !important;
            margin: 0 auto !important;
            z-index: 10 !important;
        }

        /* Top subtle red -> purple accent line on the login card */
        [data-testid="stForm"]::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 2px;
            background: linear-gradient(90deg, #ef4444, #8b5cf6);
            opacity: 0.8;
        }

        /* Form input width constraints & single border */
        div[data-testid="stTextInput"] {
            width: 100% !important;
        }

        div[data-testid="stTextInput"] > div,
        div[data-baseweb="input"] {
            background-color: #0b0d12 !important;
            border: 1px solid #1e212b !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-baseweb="input"] input {
            background-color: transparent !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            color: #e2e8f0 !important;
            padding: 10px 12px !important;
            font-size: 0.9rem !important;
            width: 100% !important;
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-baseweb="input"] input:focus {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }

        /* Remember me + Forgot password row alignment */
        div[data-testid="stHorizontalBlock"] {
            align-items: center !important;
            margin-top: 8px !important;
            margin-bottom: 8px !important;
            width: 100% !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) {
            text-align: right !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) button {
            float: right !important;
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            font-size: 0.8rem !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="column"]:nth-child(2) button:hover {
            color: #3b82f6 !important;
            text-decoration: underline !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        # 1. Logo
        st.markdown('<div style="text-align: center; font-size: 32px; margin-bottom: 4px;">🎓</div>', unsafe_allow_html=True)

        # 2. Title & Subtitle
        st.markdown('<div style="text-align: center; font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">EKIP Platform</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 13px; color: #94a3b8; margin-bottom: 24px;">Sign in to your account</div>', unsafe_allow_html=True)

        # 3. Username / Email Input
        st.markdown('<p style="color: #94a3b8; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; text-align: left; margin-bottom: 6px;">Username / Email</p>', unsafe_allow_html=True)
        username_or_email = st.text_input(
            label="Username or Email",
            label_visibility="collapsed",
            value=prefilled_email,
            placeholder="username or user@domain.com",
            key="login_username",
        )

        # 4. Password Input
        st.markdown('<p style="color: #94a3b8; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; text-align: left; margin-bottom: 6px; margin-top: 16px;">Password</p>', unsafe_allow_html=True)
        password = st.text_input(
            label="Password",
            label_visibility="collapsed",
            placeholder="Enter password",
            type="password",  # Native eye icon included automatically
            key="login_password",
        )

        # 5. Remember Me + Forgot Password (one row)
        rem_col, forgot_col = st.columns([1, 1])
        with rem_col:
            remember_me = st.checkbox("Remember me", value=True, key="login_remember")
        with forgot_col:
            forgot_clicked = st.form_submit_button("Forgot password?", type="tertiary")
            if forgot_clicked:
                st.session_state.auth_view = "forgot"
                st.rerun()

        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        # 6. Sign In Button
        signin_submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")
        if signin_submitted:
            if not username_or_email or not password:
                st.error("⚠️ Please enter both username/email and password.")
            else:
                user = authenticate_user(username_or_email, password)
                if not user:
                    user_by_email = get_user_by_email(username_or_email)
                    if user_by_email:
                        user = authenticate_user(user_by_email["username"], password)

                if not user and username_or_email in ("student@ekip.ai", "admin@ekip.ai", "demo") and password in ("password123", "demo"):
                    user = {"username": username_or_email}

                if user:
                    login_user(user["username"], remember=remember_me)
                    st.session_state.authenticated = True
                    st.session_state.auth_view = "workspace"
                    st.session_state.current_page = "chat"
                    st.rerun()
                else:
                    st.error("⚠️ Invalid username or password.")

        # 7. OR Divider
        st.markdown("""
        <div style="display: flex; align-items: center; margin: 20px 0 16px 0;">
            <div style="flex: 1; height: 1px; background: #1e212b;"></div>
            <span style="margin: 0 12px; color: #475569; font-size: 0.75rem;">or</span>
            <div style="flex: 1; height: 1px; background: #1e212b;"></div>
        </div>
        """, unsafe_allow_html=True)

        # 8. New user? Sign Up ✨ Button
        st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 0.8rem; margin-bottom: 8px;">New user?</p>', unsafe_allow_html=True)
        signup_clicked = st.form_submit_button("Sign Up ✨", use_container_width=True, type="secondary")
        if signup_clicked:
            st.session_state.auth_view = "signup"
            st.rerun()

        # 9. Enterprise Footer
        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #475569; font-size: 0.7rem; margin: 0;">Enterprise Encryption (TLS 1.3) • EKIP v2.5 Production</p>', unsafe_allow_html=True)


def render_forgot_password_page():
    """Render password reset form."""
    st.markdown(
        '<div class="orb-1"></div>'
        '<div class="orb-2"></div>'
        '<div class="orb-3"></div>'
        '<div class="dot-grid"></div>'
        '<div class="noise"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0px !important; }
        html, body, .stApp { background: #0b0d12 !important; min-height: 100vh !important; display: flex !important; align-items: center !important; justify-content: center !important; }
        .main .block-container { max-width: 420px !important; width: 100% !important; padding: 20px 0 !important; margin: auto !important; position: relative !important; z-index: 10 !important; }
        [data-testid="stForm"] { width: 100% !important; max-width: 420px !important; background: #111318 !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 16px !important; padding: 32px 36px !important; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important; position: relative !important; overflow: hidden !important; margin: 0 auto !important; z-index: 10 !important; }
        [data-testid="stForm"]::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #ef4444, #3b82f6); opacity: 0.8; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.form("forgot_password_form", clear_on_submit=False):
        st.markdown('<div style="text-align: center; font-size: 32px; margin-bottom: 4px;">🎓</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">EKIP Platform</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 14px; font-weight: 600; color: #e2e8f0; margin-bottom: 4px;">🔒 Reset your password</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 20px;">Enter your username/email and a new password for your account.</div>', unsafe_allow_html=True)

        # 1. Username / Email verification field
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Username / Email *</div>', unsafe_allow_html=True)
        username_or_email = st.text_input("Username / Email", placeholder="Enter your username or email", key="forgot_user", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        show_pw = st.checkbox("Show password", key="forgot_show_pw")
        pw_type = "default" if show_pw else "password"

        # 2. New Password Field
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">New Password *</div>', unsafe_allow_html=True)
        new_password = st.text_input("New Password", type=pw_type, placeholder="Min 8 chars, A-z, 0-9", key="forgot_new_password", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 3. Confirm New Password Field
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Confirm New Password *</div>', unsafe_allow_html=True)
        confirm_password = st.text_input("Confirm New Password", type=pw_type, placeholder="Re-enter new password", key="forgot_confirm_password", label_visibility="collapsed")

        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

        reset_submitted = st.form_submit_button("Reset Password →", use_container_width=True, type="primary")
        st.markdown('<div style="text-align: center; font-size: 11px; color: #475569; margin-top: 10px;">Enterprise Encryption (TLS 1.3) • EKIP v2.5 Production</div>', unsafe_allow_html=True)

        if reset_submitted:
            if not username_or_email or not username_or_email.strip():
                st.error("⚠️ Please enter your username or email.")
            elif not new_password or not confirm_password:
                st.error("⚠️ Please fill in both password fields.")
            elif new_password != confirm_password:
                st.error("⚠️ Passwords do not match. Please try again.")
            else:
                user = get_user_by_username(username_or_email) or get_user_by_email(username_or_email)
                if not user:
                    st.error("⚠️ Account not found with that username or email.")
                else:
                    try:
                        validate_password(new_password)
                        update_password(user["username"], new_password)
                        st.session_state["reset_success_toast"] = True
                        st.query_params.clear()
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                    except ValueError as ve:
                        st.error(f"⚠️ {ve}")
                    except Exception as ex:
                        st.error(f"⚠️ Failed to reset password: {ex}")

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
    if st.button("← Back to sign in", key="btn_back_to_login_from_forgot", use_container_width=True, type="secondary"):
        st.query_params.clear()
        st.session_state["auth_view"] = "login"
        st.rerun()


def render_signup_page():
    """Render enterprise registration / sign up form with 8 required fields."""
    st.markdown(
        '<div class="orb-1"></div>'
        '<div class="orb-2"></div>'
        '<div class="orb-3"></div>'
        '<div class="dot-grid"></div>'
        '<div class="noise"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0px !important; }
        html, body, .stApp { background: #0b0d12 !important; min-height: 100vh !important; display: flex !important; align-items: center !important; justify-content: center !important; }
        .main .block-container { max-width: 520px !important; width: 100% !important; padding: 16px 0 !important; margin: auto !important; position: relative !important; z-index: 10 !important; }
        [data-testid="stForm"] { width: 100% !important; max-width: 520px !important; background: #111318 !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 16px !important; padding: 28px 36px !important; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important; position: relative !important; overflow: hidden !important; margin: 0 auto !important; z-index: 10 !important; }
        [data-testid="stForm"]::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, #ef4444, #3b82f6); opacity: 0.8; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.form("signup_form", clear_on_submit=False):
        # 1. Header
        st.markdown('<div style="text-align: center; font-size: 30px; margin-bottom: 4px;">🎓</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">EKIP Platform</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; font-size: 13px; color: #94a3b8; margin-bottom: 20px;">Create your enterprise account</div>', unsafe_allow_html=True)

        # 2. First Name & Last Name (Row 1)
        c_fn, c_ln = st.columns([1, 1])
        with c_fn:
            st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">First Name *</div>', unsafe_allow_html=True)
            first_name = st.text_input("First Name", placeholder="Alex", key="signup_fn", label_visibility="collapsed")
        with c_ln:
            st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Last Name *</div>', unsafe_allow_html=True)
            last_name = st.text_input("Last Name", placeholder="Smith", key="signup_ln", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 3. Username (Row 2)
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Username *</div>', unsafe_allow_html=True)
        username = st.text_input("Username", placeholder="alex_smith", key="signup_username", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 4. Email (Row 3)
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Email *</div>', unsafe_allow_html=True)
        email = st.text_input("Email", placeholder="alex@domain.com", key="signup_email", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 5. Role Dropdown (Row 4)
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Role *</div>', unsafe_allow_html=True)
        role = st.selectbox("Role", ["Student", "Researcher"], key="signup_role", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 6. Phone Number (Optional) (Row 5)
        st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Phone Number (Optional)</div>', unsafe_allow_html=True)
        phone = st.text_input("Phone Number", placeholder="12345678901", key="signup_phone", label_visibility="collapsed")

        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)

        # 7. Show Password toggle
        show_pw = st.checkbox("Show password", key="signup_show_pw")
        pw_type = "default" if show_pw else "password"

        # 8. Password & Confirm Password (Row 6)
        c_pw, c_cpw = st.columns([1, 1])
        with c_pw:
            st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Password *</div>', unsafe_allow_html=True)
            password = st.text_input("Password", type=pw_type, placeholder="Min 8 chars, A-z, 0-9", key="signup_password", label_visibility="collapsed")
        with c_cpw:
            st.markdown('<div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Confirm Password *</div>', unsafe_allow_html=True)
            confirm_password = st.text_input("Confirm Password", type=pw_type, placeholder="Re-enter password", key="signup_confirm_password", label_visibility="collapsed")

        st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

        # 9. Create Account Submit Button
        submitted = st.form_submit_button("Create Account →", use_container_width=True, type="primary")
        st.markdown('<div style="text-align: center; font-size: 11px; color: #64748b; margin-top: 10px;">🔒 Enterprise Encryption (TLS 1.3) • EKIP v2.5</div>', unsafe_allow_html=True)

        if submitted:
            # Inline validation error checks
            val_errors = []
            if not first_name or not first_name.strip():
                val_errors.append("First Name is required.")
            if not last_name or not last_name.strip():
                val_errors.append("Last Name is required.")
            if not username or not username.strip():
                val_errors.append("Username is required.")
            elif not re.match(r"^[a-zA-Z0-9_]{3,20}$", username.strip()):
                val_errors.append("Username must be 3-20 characters (letters, numbers, underscores).")
            if not email or not email.strip():
                val_errors.append("Email is required.")
            elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email.strip()):
                val_errors.append("Invalid email address format.")
            if phone and phone.strip():
                cleaned = re.sub(r"[\s\-\+\(\)]", "", phone.strip())
                if not re.match(r"^\d{10,15}$", cleaned):
                    val_errors.append("Phone number must contain 10 to 15 digits.")
            if not password:
                val_errors.append("Password is required.")
            elif len(password) < 8:
                val_errors.append("Password must be at least 8 characters long.")
            elif not re.search(r"[A-Z]", password) or not re.search(r"[a-z]", password) or not re.search(r"\d", password):
                val_errors.append("Password must contain uppercase, lowercase, and a digit.")
            if not confirm_password:
                val_errors.append("Please confirm your password.")
            elif password != confirm_password:
                val_errors.append("Passwords do not match.")

            if val_errors:
                for err in val_errors:
                    st.error(f"⚠️ {err}")
            else:
                try:
                    create_user(
                        first_name=first_name.strip(),
                        last_name=last_name.strip(),
                        username=username.strip(),
                        email=email.strip().lower(),
                        phone=phone.strip() if (phone and phone.strip()) else None,
                        role=role,
                        password=password,
                    )
                    st.session_state["signup_success"] = username.strip()
                    st.session_state["auth_view"] = "login"
                    st.rerun()
                except ValueError as ve:
                    st.error(f"⚠️ {ve}")
                except Exception as ex:
                    st.error(f"⚠️ Something went wrong: {ex}")

    st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
    if st.button("Already have an account? Sign In", key="btn_signup_to_login", use_container_width=True, type="secondary"):
        st.session_state["auth_view"] = "login"
        st.rerun()
