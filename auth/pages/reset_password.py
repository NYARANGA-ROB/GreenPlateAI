"""
Password reset page for GreenPlateAI authentication.

This module provides the Streamlit password reset interface with
token-based password recovery functionality.
"""

import streamlit as st
import time
from typing import Optional

from auth.auth_utils import auth_manager
from utils.helpers import get_client_ip, get_user_agent


def show_reset_password_page():
    """Display the password reset page."""
    
    # Page configuration
    st.set_page_config(
        page_title="Reset Password - GreenPlateAI",
        page_icon="🔑",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .reset-container {
            max-width: 450px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .reset-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .reset-title {
            color: #2E8B57;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .reset-subtitle {
            color: #666;
            font-size: 1rem;
        }
        .error-message {
            background-color: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border: 1px solid #f5c6cb;
        }
        .success-message {
            background-color: #d4edda;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border: 1px solid #c3e6cb;
        }
        .info-message {
            background-color: #d1ecf1;
            color: #0c5460;
            padding: 1rem;
            border-radius: 5px;
            margin-bottom: 1rem;
            border: 1px solid #bee5eb;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Check if user is already logged in
    if 'session_token' in st.session_state and st.session_state.session_token:
        user = auth_manager.get_current_user(st.session_state.session_token)
        if user:
            st.success(f"You are already logged in as {user.full_name or user.username}!")
            st.info("You can change your password from your profile settings.")
            st.info("Redirecting to dashboard...")
            time.sleep(2)
            st.switch_page("app.py")
            return
    
    # Password reset flow
    if 'reset_token' not in st.session_state:
        show_reset_request_form()
    else:
        show_password_reset_form()


def show_reset_request_form():
    """Show password reset request form."""
    
    with st.container():
        st.markdown("""
            <div class="reset-container">
                <div class="reset-header">
                    <div class="reset-title">🔑 Reset Password</div>
                    <div class="reset-subtitle">Forgot your password? No problem!</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Reset request form
        with st.form("reset_request_form"):
            st.subheader("📧 Request Password Reset")
            
            st.info("""
            **How it works:**
            1. Enter your registered email address
            2. We'll send you a password reset link
            3. Click the link to reset your password
            4. The link expires after 1 hour for security
            """)
            
            email = st.text_input(
                "Email Address",
                placeholder="Enter your registered email",
                key="reset_email",
                help="Enter the email address associated with your account"
            )
            
            # Submit button
            submit_button = st.form_submit_button(
                "Send Reset Link",
                type="primary",
                use_container_width=True
            )
            
            if submit_button:
                if not email:
                    st.error("Please enter your email address")
                    return
                
                # Validate email format
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    st.error("Please enter a valid email address")
                    return
                
                # Request password reset
                success, message = auth_manager.reset_password_request(email)
                
                if success:
                    st.markdown(f"""
                        <div class="success-message">
                            <strong>Reset Link Sent!</strong><br>
                            {message}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("""
                    **Next Steps:**
                    1. Check your email inbox (and spam folder)
                    2. Click the password reset link
                    3. Create a new password
                    4. Login with your new password
                    
                    **Note:** The reset link will expire in 1 hour for security reasons.
                    """)
                    
                    # Simulate receiving the token (for demo purposes)
                    st.markdown("---")
                    st.markdown("### 🎯 Demo Mode")
                    st.info("For demo purposes, you can simulate receiving the reset link:")
                    
                    if st.button("📥 Simulate Receiving Reset Link", use_container_width=True):
                        # Generate a demo token
                        import secrets
                        demo_token = secrets.token_urlsafe(32)
                        st.session_state.reset_token = demo_token
                        st.session_state.reset_email = email
                        st.rerun()
                    
                else:
                    st.markdown(f"""
                        <div class="error-message">
                            <strong>Reset Request Failed</strong><br>
                            {message}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 **Troubleshooting:**")
                    st.write("- Check that you entered the correct email address")
                    st.write("- Make sure you're using your registered email")
                    st.write("- Contact support if you continue to have issues")
        
        # Additional options
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔐 Back to Login", use_container_width=True):
                st.switch_page("auth/pages/login.py")
        
        with col2:
            if st.button("📝 Register Account", use_container_width=True):
                st.switch_page("auth/pages/register.py")


def show_password_reset_form():
    """Show password reset form with token."""
    
    # Get token and email from session state
    reset_token = st.session_state.get('reset_token')
    reset_email = st.session_state.get('reset_email')
    
    if not reset_token:
        st.error("Invalid reset token. Please request a new password reset.")
        st.session_state.clear()
        time.sleep(2)
        st.switch_page("auth/pages/reset_password.py")
        return
    
    with st.container():
        st.markdown("""
            <div class="reset-container">
                <div class="reset-header">
                    <div class="reset-title">🔑 Reset Password</div>
                    <div class="reset-subtitle">Create your new password</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Show email being reset
        st.info(f"📧 Resetting password for: **{reset_email}**")
        
        # Password reset form
        with st.form("password_reset_form"):
            st.subheader("🔐 Create New Password")
            
            # Password inputs
            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter your new password",
                key="new_password",
                help="Create a strong password with at least 8 characters"
            )
            
            confirm_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter your new password",
                key="confirm_new_password",
                help="Re-enter your new password to confirm"
            )
            
            # Password strength indicator
            if new_password:
                from auth.auth_utils import PasswordManager
                password_validation = PasswordManager.validate_password_strength(new_password)
                
                strength_class = "strength-weak"
                strength_color = "#f8d7da"
                if password_validation["score"] >= 70:
                    strength_class = "strength-strong"
                    strength_color = "#d4edda"
                elif password_validation["score"] >= 40:
                    strength_class = "strength-medium"
                    strength_color = "#fff3cd"
                
                st.markdown(f"""
                    <div class="password-strength {strength_class}" style="background-color: {strength_color};">
                        <strong>Password Strength:</strong> {password_validation["score"]}/100
                        {f"<br>• {', '.join(password_validation['errors'])}" if password_validation['errors'] else ""}
                    </div>
                """, unsafe_allow_html=True)
            
            # Security reminder
            st.markdown("""
            <div class="info-message">
                <strong>🔒 Security Reminder:</strong>
                - Use a unique password that you haven't used before
                - Include uppercase, lowercase, numbers, and special characters
                - Don't share your password with anyone
                - Consider using a password manager
            </div>
            """, unsafe_allow_html=True)
            
            # Submit buttons
            col1, col2 = st.columns(2)
            
            with col1:
                submit_button = st.form_submit_button(
                    "Reset Password",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                cancel_button = st.form_submit_button(
                    "Cancel",
                    use_container_width=True
                )
            
            if submit_button:
                # Validate form
                if not new_password or not confirm_password:
                    st.error("Please enter and confirm your new password")
                    return
                
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                    return
                
                # Validate password strength
                password_validation = PasswordManager.validate_password_strength(new_password)
                if not password_validation['valid']:
                    st.error("Password does not meet security requirements:")
                    for error in password_validation['errors']:
                        st.error(f"• {error}")
                    return
                
                # Reset password
                success, message = auth_manager.reset_password(reset_token, new_password)
                
                if success:
                    st.markdown(f"""
                        <div class="success-message">
                            <strong>Password Reset Successful!</strong><br>
                            {message}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("""
                    **Your password has been reset successfully!**
                    
                    You can now login with your new password.
                    """)
                    
                    # Clear session state
                    if 'reset_token' in st.session_state:
                        del st.session_state.reset_token
                    if 'reset_email' in st.session_state:
                        del st.session_state.reset_email
                    
                    # Auto-login option
                    if st.button("🚀 Login Now", use_container_width=True):
                        # Authenticate with new password
                        auth_success, auth_message, auth_user, session_token = auth_manager.authenticate_user(
                            email=reset_email,
                            password=new_password,
                            ip_address=get_client_ip(),
                            user_agent=get_user_agent()
                        )
                        
                        if auth_success and auth_user and session_token:
                            st.session_state.session_token = session_token
                            st.session_state.user = auth_user.to_dict()
                            st.session_state.login_time = time.time()
                            
                            st.success("Login successful! Redirecting...")
                            time.sleep(1.5)
                            st.switch_page("app.py")
                        else:
                            st.error(f"Auto-login failed: {auth_message}")
                            st.info("Please login manually.")
                            time.sleep(2)
                            st.switch_page("auth/pages/login.py")
                    
                    # Manual login option
                    if st.button("🔐 Go to Login Page", use_container_width=True):
                        st.switch_page("auth/pages/login.py")
                    
                else:
                    st.markdown(f"""
                        <div class="error-message">
                            <strong>Password Reset Failed</strong><br>
                            {message}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.info("💡 **Troubleshooting:**")
                    st.write("- The reset link may have expired")
                    st.write("- The link may have already been used")
                    st.write("- Try requesting a new password reset")
                    
                    if st.button("🔄 Request New Reset Link", use_container_width=True):
                        if 'reset_token' in st.session_state:
                            del st.session_state.reset_token
                        if 'reset_email' in st.session_state:
                            del st.session_state.reset_email
                        st.rerun()
            
            elif cancel_button:
                # Clear session state and go back
                if 'reset_token' in st.session_state:
                    del st.session_state.reset_token
                if 'reset_email' in st.session_state:
                    del st.session_state.reset_email
                
                st.info("Password reset cancelled.")
                time.sleep(1)
                st.switch_page("auth/pages/login.py")
        
        # Additional options
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔐 Back to Login", use_container_width=True):
                if 'reset_token' in st.session_state:
                    del st.session_state.reset_token
                if 'reset_email' in st.session_state:
                    del st.session_state.reset_email
                st.switch_page("auth/pages/login.py")
        
        with col2:
            if st.button("📝 Register Account", use_container_width=True):
                if 'reset_token' in st.session_state:
                    del st.session_state.reset_token
                if 'reset_email' in st.session_state:
                    del st.session_state.reset_email
                st.switch_page("auth/pages/register.py")


def show_change_password_form():
    """Show password change form for authenticated users."""
    
    user_info = st.session_state.get('user')
    if not user_info:
        st.error("You must be logged in to change your password.")
        return
    
    with st.expander("🔑 Change Password", expanded=False):
        st.markdown("### Update Your Password")
        
        with st.form("change_password_form"):
            # Current password
            current_password = st.text_input(
                "Current Password",
                type="password",
                placeholder="Enter your current password",
                key="current_password",
                help="Enter your current password for verification"
            )
            
            # New password
            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter your new password",
                key="new_password_change",
                help="Create a strong new password"
            )
            
            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Re-enter your new password",
                key="confirm_new_password",
                help="Re-enter your new password to confirm"
            )
            
            # Submit button
            submit_button = st.form_submit_button("Change Password", type="primary")
            
            if submit_button:
                if not current_password or not new_password or not confirm_new_password:
                    st.error("Please fill in all password fields")
                    return
                
                if new_password != confirm_new_password:
                    st.error("New passwords do not match")
                    return
                
                # Change password
                success, message = auth_manager.change_password(
                    user_id=user_info['id'],
                    current_password=current_password,
                    new_password=new_password
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.info("You will need to login again with your new password.")
                    
                    if st.button("🚀 Logout and Login Again"):
                        from auth.pages.login import logout_user
                        logout_user()
                else:
                    st.error(f"❌ {message}")


# Main execution
if __name__ == "__main__":
    show_reset_password_page()
