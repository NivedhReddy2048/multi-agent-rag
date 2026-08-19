"""Profile Page component for EKIP Platform."""

import streamlit as st
from datetime import datetime
from core.auth.session import logout_user


def render_profile_page():
    """Renders enterprise read-only user profile page with vertical auto-scrolling."""
    # Scope vertical scrolling specifically for the Profile page main container
    st.markdown(
        """
        <style>
        [data-testid="stMain"], .main, .main .block-container {
            overflow-y: auto !important;
            max-height: none !important;
            height: auto !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user = st.session_state.get("user", {}) or {}

    first_name = user.get("first_name", "User")
    last_name = user.get("last_name", "")
    username = user.get("username", "")
    email = user.get("email", "")
    phone = user.get("phone", "Not provided")
    role = user.get("role", "Student")

    created = user.get("created_at")
    if isinstance(created, datetime):
        created_at = created.strftime("%b %Y")
    elif isinstance(created, str) and len(created) >= 7:
        created_at = created[:10]
    else:
        created_at = "2026"

    # Back button (native Streamlit)
    if st.button("← Back", key="profile_back"):
        st.session_state.current_page = "chat"
        st.rerun()

    initials = f"{first_name[0]}{last_name[0]}" if (last_name and len(last_name) > 0) else (first_name[0] if len(first_name) > 0 else "U")

    profile_img_b64 = user.get("profile_image_b64")
    if profile_img_b64:
        avatar_dom = f'<div style="width:120px;height:120px;border-radius:50%;margin:0 auto 16px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.3);border:2px solid #3b82f6;"><img src="data:image/png;base64,{profile_img_b64}" style="width:100%;height:100%;object-fit:cover;display:block;" /></div>'
    else:
        avatar_dom = f'<div style="width:120px;height:120px;border-radius:50%;background:linear-gradient(135deg,#3b82f6,#8b5cf6);display:flex;align-items:center;justify-content:center;margin:0 auto 16px;color:white;font-size:2rem;font-weight:700;">{initials}</div>'

    # Build HTML as single string — NO indentation, NO newlines at start
    html_content = (
        '<div style="max-width:480px;margin:20px auto;background:#111318;border:1px solid #1e212b;border-radius:16px;padding:32px;text-align:center;font-family:system-ui,-apple-system,sans-serif;">'
        + avatar_dom
        + f'<div style="font-size:1.5rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">{first_name} {last_name}</div>'
        + f'<div style="font-size:0.9rem;color:#94a3b8;margin-bottom:12px;">{email}</div>'
        + f'<div style="margin-bottom:24px;"><span style="background:rgba(59,130,246,0.15);color:#3b82f6;padding:4px 14px;border-radius:20px;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;border:1px solid rgba(59,130,246,0.3);">{role}</span></div>'
        + '<div style="border-top:1px solid #1e212b;margin:20px 0;"></div>'
        + '<div style="text-align:left;margin-bottom:24px;">'
        + f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e212b;"><span style="color:#94a3b8;font-weight:500;font-size:0.88rem;">📛 Username</span><span style="color:#e2e8f0;font-weight:600;font-size:0.88rem;">{username}</span></div>'
        + f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e212b;"><span style="color:#94a3b8;font-weight:500;font-size:0.88rem;">📧 Email</span><span style="color:#e2e8f0;font-weight:600;font-size:0.88rem;">{email}</span></div>'
        + f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e212b;"><span style="color:#94a3b8;font-weight:500;font-size:0.88rem;">📞 Phone</span><span style="color:#e2e8f0;font-weight:600;font-size:0.88rem;">{phone}</span></div>'
        + f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1e212b;"><span style="color:#94a3b8;font-weight:500;font-size:0.88rem;">🎓 Role</span><span style="color:#e2e8f0;font-weight:600;font-size:0.88rem;">{role}</span></div>'
        + f'<div style="display:flex;justify-content:space-between;padding:10px 0;"><span style="color:#94a3b8;font-weight:500;font-size:0.88rem;">📅 Joined</span><span style="color:#e2e8f0;font-weight:600;font-size:0.88rem;">{created_at}</span></div>'
        + '</div>'
        + '</div>'
    )

    # Native Streamlit markdown allows dynamic height and vertical scrolling without clipping
    st.markdown(html_content, unsafe_allow_html=True)

    # Logout button below the card
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚪 Logout", key="profile_logout", type="primary", use_container_width=True):
            logout_user()
            st.session_state["auth_view"] = "cover"
            st.session_state["current_page"] = "chat"
            st.session_state["show_profile_dropdown"] = False
            st.rerun()

