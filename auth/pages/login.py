"""
Login page for GreenPlateAI authentication.

This module provides the Streamlit login interface with
form validation and authentication logic.
"""

import streamlit as st
import time
from typing import Optional

from auth.auth_utils import auth_manager
from utils.helpers import get_client_ip, get_user_agent


def show_login_page():
    """Display the login page."""
    
    # Page configuration
    st.set_page_config(
        page_title="Login - GreenPlateAI",
        page_icon="🔐",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-title {
            color: #2E8B57;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .login-subtitle {
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
        </style>
    """, unsafe_allow_html=True)
    
    # Check if user is already logged in
    if 'session_token' in st.session_state and st.session_state.session_token:
        user = auth_manager.get_current_user(st.session_state.session_token)
        if user:
            st.success(f"Welcome back, {user.full_name or user.username}!")
            st.info("You are already logged in. Redirecting to dashboard...")
            time.sleep(2)
            st.switch_page("app.py")
            return
    
    # Login form
    with st.container():
        st.markdown("""
            <div class="login-container">
                <div class="login-header">
                    <div class="login-title">🥗 GreenPlateAI</div>
                    <div class="login-subtitle">University Food Waste Management</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Login form
        with st.form("login_form"):
            st.subheader("🔐 Login")
            
            # Email input
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email",
                key="login_email",
                help="Enter your registered email address"
            )
            
            # Password input
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
                help="Enter your password"
            )
            
            # Remember me checkbox
            remember_me = st.checkbox("Remember me", key="remember_me")
            
            # Submit button
            submit_button = st.form_submit_button(
                "Login",
                type="primary",
                use_container_width=True
            )
            
            if submit_button:
                # Validate inputs
                if not email or not password:
                    st.error("Please enter both email and password")
                    return
                
                # Authenticate user
                success, message, user, session_token = auth_manager.authenticate_user(
                    email=email,
                    password=password,
                    ip_address=get_client_ip(),
                    user_agent=get_user_agent()
                )
                
                if success and user and session_token:
                    # Store session in session state
                    st.session_state.session_token = session_token
                    st.session_state.user = user.to_dict()
                    st.session_state.login_time = time.time()
                    
                    if remember_me:
                        st.session_state.remember_me = True
                    
                    # Show success message
                    st.markdown(f"""
                        <div class="success-message">
                            <strong>Login successful!</strong><br>
                            Welcome back, {user.full_name or user.username}!
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Redirect to main app
                    time.sleep(1.5)
                    st.switch_page("app.py")
                    
                else:
                    # Show error message
                    st.markdown(f"""
                        <div class="error-message">
                            <strong>Login Failed</strong><br>
                            {message}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Add helpful hints
                    if "Invalid email or password" in message:
                        st.info("💡 **Tips:**")
                        st.write("- Check that your email and password are correct")
                        st.write("- Make sure Caps Lock is off")
                        st.write("- Try resetting your password if you've forgotten it")
    
    # Additional options
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📝 Register", use_container_width=True):
            st.switch_page("auth/pages/register.py")
    
    with col2:
        if st.button("🔑 Forgot Password", use_container_width=True):
            st.switch_page("auth/pages/reset_password.py")
    
    # Demo account information
    with st.expander("🎯 Demo Account", expanded=False):
        st.info("""
        **Demo Login Credentials:**
        - **Email:** admin@greenplateai.com
        - **Password:** admin123
        - **Role:** Administrator
        
        **Other Demo Accounts:**
        - **Kitchen Staff:** kitchen@greenplateai.com / kitchen123
        - **Student:** student@greenplateai.com / student123
        """)


def show_login_form_simple():
    """Show a simplified login form for embedding in other pages."""
    
    with st.form("simple_login_form"):
        st.subheader("🔐 Quick Login")
        
        email = st.text_input("Email", key="simple_email")
        password = st.text_input("Password", type="password", key="simple_password")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Login", type="primary")
        
        with col2:
            if st.button("Register", key="simple_register"):
                st.switch_page("auth/pages/register.py")
        
        if submitted:
            if not email or not password:
                st.error("Please enter email and password")
                return None
            
            success, message, user, session_token = auth_manager.authenticate_user(
                email=email,
                password=password,
                ip_address=get_client_ip(),
                user_agent=get_user_agent()
            )
            
            if success and user and session_token:
                st.session_state.session_token = session_token
                st.session_state.user = user.to_dict()
                st.session_state.login_time = time.time()
                
                st.success(f"Welcome back, {user.full_name or user.username}!")
                st.rerun()
                
            else:
                st.error(message)
                return None
        
        return st.session_state.get('session_token')


def check_authentication() -> Optional[dict]:
    """Check if user is authenticated and return user info."""
    session_token = st.session_state.get('session_token')
    
    if not session_token:
        return None
    
    user = auth_manager.get_current_user(session_token)
    
    if not user:
        # Clear invalid session
        if 'session_token' in st.session_state:
            del st.session_state.session_token
        if 'user' in st.session_state:
            del st.session_state.user
        return None
    
    # Update user info in session state
    st.session_state.user = user.to_dict()
    
    return user.to_dict()


def logout_user():
    """Logout the current user."""
    session_token = st.session_state.get('session_token')
    
    if session_token:
        auth_manager.logout_user(session_token)
    
    # Clear session state
    if 'session_token' in st.session_state:
        del st.session_state.session_token
    if 'user' in st.session_state:
        del st.session_state.user
    if 'login_time' in st.session_state:
        del st.session_state.login_time
    
    st.success("Logged out successfully!")
    time.sleep(1)
    st.switch_page("auth/pages/login.py")


def show_logout_button():
    """Show logout button in sidebar."""
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        logout_user()


def show_user_info():
    """Show current user information in sidebar."""
    user_info = check_authentication()
    
    if user_info:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 👤 User Information")
        st.sidebar.write(f"**Name:** {user_info.get('full_name', 'N/A')}")
        st.sidebar.write(f"**Email:** {user_info.get('email', 'N/A')}")
        st.sidebar.write(f"**Role:** {user_info.get('role', 'N/A').title()}")
        
        # Last login info
        if user_info.get('last_login'):
            last_login = user_info['last_login'][:19]  # Remove microseconds
            st.sidebar.write(f"**Last Login:** {last_login}")
        
        # Login count
        login_count = user_info.get('login_count', 0)
        st.sidebar.write(f"**Login Count:** {login_count}")
        
        show_logout_button()


# Main execution
if __name__ == "__main__":
    show_login_page()
