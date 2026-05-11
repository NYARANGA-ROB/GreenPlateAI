"""
Registration page for GreenPlateAI authentication.

This module provides the Streamlit registration interface with
form validation and user creation logic.
"""

import streamlit as st
import re
import time
from typing import Dict, Any

from auth.auth_utils import auth_manager, PasswordManager
from models.user_auth import UserRole
from utils.helpers import get_client_ip, get_user_agent


def show_registration_page():
    """Display the registration page."""
    
    # Page configuration
    st.set_page_config(
        page_title="Register - GreenPlateAI",
        page_icon="📝",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .register-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .register-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .register-title {
            color: #2E8B57;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .register-subtitle {
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
        .password-strength {
            margin-top: 0.5rem;
            padding: 0.5rem;
            border-radius: 5px;
            font-size: 0.9rem;
        }
        .strength-weak {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .strength-medium {
            background-color: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        .strength-strong {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Check if user is already logged in
    if 'session_token' in st.session_state and st.session_state.session_token:
        user = auth_manager.get_current_user(st.session_state.session_token)
        if user:
            st.success(f"You are already logged in as {user.full_name or user.username}!")
            st.info("Redirecting to dashboard...")
            time.sleep(2)
            st.switch_page("app.py")
            return
    
    # Registration form
    with st.container():
        st.markdown("""
            <div class="register-container">
                <div class="register-header">
                    <div class="register-title">🥗 GreenPlateAI</div>
                    <div class="register-subtitle">Create Your Account</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Registration form
        with st.form("registration_form"):
            st.subheader("📝 Create Account")
            
            # Personal Information Section
            st.markdown("### 👤 Personal Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input(
                    "Full Name",
                    placeholder="Enter your full name",
                    key="reg_full_name",
                    help="Enter your complete name"
                )
            
            with col2:
                email = st.text_input(
                    "Email Address",
                    placeholder="your.email@university.edu",
                    key="reg_email",
                    help="Use your university email address"
                )
            
            # Account Information Section
            st.markdown("### 🔐 Account Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input(
                    "Username",
                    placeholder="Choose a username",
                    key="reg_username",
                    help="3-30 characters, letters, numbers, and underscores only"
                )
            
            with col2:
                phone = st.text_input(
                    "Phone Number",
                    placeholder="+1234567890",
                    key="reg_phone",
                    help="Optional: Enter your phone number"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Create a strong password",
                    key="reg_password",
                    help="Minimum 8 characters with uppercase, lowercase, numbers, and special characters"
                )
            
            with col2:
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm_password",
                    help="Re-enter your password to confirm"
                )
            
            # Password strength indicator
            if password:
                password_validation = PasswordManager.validate_password_strength(password)
                strength_class = "strength-weak"
                if password_validation["score"] >= 70:
                    strength_class = "strength-strong"
                elif password_validation["score"] >= 40:
                    strength_class = "strength-medium"
                
                st.markdown(f"""
                    <div class="password-strength {strength_class}">
                        <strong>Password Strength:</strong> {password_validation["score"]}/100
                        {f"<br>• {', '.join(password_validation['errors'])}" if password_validation['errors'] else ""}
                    </div>
                """, unsafe_allow_html=True)
            
            # Role Selection Section
            st.markdown("### 🎭 Role Selection")
            
            role = st.selectbox(
                "Select Your Role",
                options=[
                    ("student", UserRole.STUDENT),
                    ("kitchen_staff", UserRole.KITCHEN_STAFF),
                    ("admin", UserRole.ADMIN)
                ],
                format_func=lambda x: x[1].title().replace("_", " "),
                key="reg_role",
                help="Select your role in the university food service"
            )
            
            # Department (for staff roles)
            department = ""
            if role[1] in [UserRole.KITCHEN_STAFF, UserRole.ADMIN]:
                department = st.text_input(
                    "Department",
                    placeholder="e.g., Food Services, Administration",
                    key="reg_department",
                    help="Enter your department or unit"
                )
            
            # Terms and Conditions
            st.markdown("### 📋 Terms and Conditions")
            
            agree_terms = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                key="agree_terms",
                help="You must agree to the terms to create an account"
            )
            
            # Terms preview
            with st.expander("📄 View Terms and Privacy Policy"):
                st.markdown("""
                **Terms of Service:**
                - You must use the system for legitimate university food waste management purposes
                - You are responsible for maintaining the confidentiality of your account
                - You must not share your login credentials with others
                - You must report any security issues immediately
                
                **Privacy Policy:**
                - We collect only necessary information for system functionality
                - Your data is stored securely and used only for system operations
                - We do not share your personal information with third parties
                - You can request data deletion at any time
                """)
            
            # Submit button
            submit_button = st.form_submit_button(
                "Create Account",
                type="primary",
                use_container_width=True
            )
            
            if submit_button:
                # Validate form
                validation_result = validate_registration_form({
                    'full_name': full_name,
                    'email': email,
                    'username': username,
                    'phone': phone,
                    'password': password,
                    'confirm_password': confirm_password,
                    'role': role[1],
                    'department': department,
                    'agree_terms': agree_terms
                })
                
                if not validation_result['valid']:
                    # Display validation errors
                    st.markdown(f"""
                        <div class="error-message">
                            <strong>Registration Failed</strong><br>
                            {validation_result['message']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Show individual errors
                    for error in validation_result['errors']:
                        st.error(f"• {error}")
                else:
                    # Attempt to register user
                    success, message, user = auth_manager.register_user(
                        email=email,
                        username=username,
                        password=password,
                        full_name=full_name,
                        phone=phone if phone else None,
                        department=department if department else None,
                        role=role[1],
                        auto_verify=True  # Auto-verify for demo
                    )
                    
                    if success and user:
                        # Show success message
                        st.markdown(f"""
                            <div class="success-message">
                                <strong>Registration Successful!</strong><br>
                                Welcome to GreenPlateAI, {user.full_name or user.username}!<br>
                                You can now log in with your credentials.
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Auto-login option
                        if st.button("🚀 Login Now", use_container_width=True):
                            # Authenticate and login
                            auth_success, auth_message, auth_user, session_token = auth_manager.authenticate_user(
                                email=email,
                                password=password,
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
                                st.info("Please login manually from the login page.")
                                time.sleep(2)
                                st.switch_page("auth/pages/login.py")
                        
                        # Manual login option
                        if st.button("🔐 Go to Login Page", use_container_width=True):
                            st.switch_page("auth/pages/login.py")
                        
                    else:
                        # Show registration error
                        st.markdown(f"""
                            <div class="error-message">
                                <strong>Registration Failed</strong><br>
                                {message}
                            </div>
                        """, unsafe_allow_html=True)
    
    # Additional options
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔐 Back to Login", use_container_width=True):
            st.switch_page("auth/pages/login.py")
    
    with col2:
        if st.button("🔑 Forgot Password", use_container_width=True):
            st.switch_page("auth/pages/reset_password.py")
    
    # Help section
    with st.expander("❓ Need Help?", expanded=False):
        st.info("""
        **Registration Help:**
        - Use your university email address for faster verification
        - Choose a strong password with at least 8 characters
        - Username must be unique and contain only letters, numbers, and underscores
        - Phone number is optional but recommended for account recovery
        
        **Role Information:**
        - **Student:** View dashboards and track personal food waste
        - **Kitchen Staff:** Manage inventory, track waste, and view reports
        - **Administrator:** Full system access and user management
        
        **Having Trouble?**
        - Contact the IT support team at support@greenplateai.com
        - Check if your email is already registered
        - Ensure your password meets all security requirements
        """)


def validate_registration_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate registration form data."""
    
    errors = []
    
    # Required fields
    required_fields = ['full_name', 'email', 'username', 'password', 'confirm_password', 'agree_terms']
    for field in required_fields:
        if not form_data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    if errors:
        return {
            'valid': False,
            'message': 'Please fill in all required fields',
            'errors': errors
        }
    
    # Full name validation
    full_name = form_data['full_name']
    if len(full_name) < 2:
        errors.append("Full name must be at least 2 characters long")
    elif len(full_name) > 100:
        errors.append("Full name must be less than 100 characters")
    elif not re.match(r'^[a-zA-Z\s\-\.]+$', full_name):
        errors.append("Full name can only contain letters, spaces, hyphens, and periods")
    
    # Email validation
    email = form_data['email']
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("Please enter a valid email address")
    elif len(email) > 255:
        errors.append("Email address is too long")
    
    # Username validation
    username = form_data['username']
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    elif len(username) > 30:
        errors.append("Username must be less than 30 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers, and underscores")
    elif username.lower() in ['admin', 'root', 'system', 'test', 'demo']:
        errors.append("Username is reserved and cannot be used")
    
    # Phone validation (optional)
    phone = form_data.get('phone')
    if phone:
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, phone.replace('-', '').replace(' ', '')):
            errors.append("Please enter a valid phone number")
    
    # Password validation
    password = form_data['password']
    confirm_password = form_data['confirm_password']
    
    password_validation = PasswordManager.validate_password_strength(password)
    if not password_validation['valid']:
        errors.extend(password_validation['errors'])
    
    # Password confirmation
    if password != confirm_password:
        errors.append("Passwords do not match")
    
    # Role validation
    role = form_data.get('role')
    if role not in [UserRole.STUDENT, UserRole.KITCHEN_STAFF, UserRole.ADMIN]:
        errors.append("Invalid role selected")
    
    # Department validation (required for staff roles)
    if role in [UserRole.KITCHEN_STAFF, UserRole.ADMIN]:
        department = form_data.get('department')
        if not department:
            errors.append("Department is required for staff roles")
        elif len(department) < 2:
            errors.append("Department name must be at least 2 characters long")
    
    # Terms agreement
    if not form_data.get('agree_terms'):
        errors.append("You must agree to the terms and conditions")
    
    if errors:
        return {
            'valid': False,
            'message': 'Please correct the following errors',
            'errors': errors
        }
    
    return {
        'valid': True,
        'message': 'Validation successful',
        'errors': []
    }


def show_registration_form_simple():
    """Show a simplified registration form for embedding in other pages."""
    
    with st.form("simple_registration_form"):
        st.subheader("📝 Quick Registration")
        
        email = st.text_input("Email", key="simple_reg_email")
        username = st.text_input("Username", key="simple_reg_username")
        password = st.text_input("Password", type="password", key="simple_reg_password")
        full_name = st.text_input("Full Name", key="simple_reg_full_name")
        
        role = st.selectbox(
            "Role",
            options=[UserRole.STUDENT, UserRole.KITCHEN_STAFF, UserRole.ADMIN],
            format_func=lambda x: x.title().replace("_", " "),
            key="simple_reg_role"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Register", type="primary")
        
        with col2:
            if st.button("Login", key="simple_login"):
                st.switch_page("auth/pages/login.py")
        
        if submitted:
            form_data = {
                'full_name': full_name,
                'email': email,
                'username': username,
                'password': password,
                'confirm_password': password,
                'role': role,
                'department': '',
                'agree_terms': True
            }
            
            validation_result = validate_registration_form(form_data)
            
            if not validation_result['valid']:
                for error in validation_result['errors']:
                    st.error(error)
                return None
            
            success, message, user = auth_manager.register_user(
                email=email,
                username=username,
                password=password,
                full_name=full_name,
                role=role
            )
            
            if success and user:
                st.success(f"Registration successful! Welcome, {user.full_name or user.username}!")
                st.info("Please login to continue.")
                time.sleep(2)
                st.switch_page("auth/pages/login.py")
            else:
                st.error(message)
                return None
        
        return None


# Main execution
if __name__ == "__main__":
    show_registration_page()
