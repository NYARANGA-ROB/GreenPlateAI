"""
Authenticated sidebar navigation for GreenPlateAI.

This module provides role-based sidebar navigation with
user information and quick actions.
"""

import streamlit as st
from typing import Dict, List, Optional
import time

from auth.auth_utils import auth_manager
from auth.access_control import check_authentication, get_user_role, UserRole
from models.user_auth import User


def show_authenticated_sidebar():
    """Display authenticated sidebar with navigation and user info."""
    
    # Check authentication
    user_info = check_authentication()
    
    if not user_info:
        show_unauthenticated_sidebar()
        return
    
    # User information section
    show_user_sidebar_section(user_info)
    
    # Navigation menu based on role
    user_role = UserRole(user_info.get('role', 'student'))
    show_navigation_menu(user_role, user_info)
    
    # Quick actions section
    show_quick_actions_section(user_info)
    
    # Footer section
    show_sidebar_footer()


def show_unauthenticated_sidebar():
    """Display sidebar for unauthenticated users."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔐 Authentication Required")
    
    st.sidebar.info("Please log in to access the full features of GreenPlateAI.")
    
    # Quick login form
    with st.sidebar.form("sidebar_login_form"):
        st.markdown("**Quick Login**")
        
        email = st.text_input("Email", key="sidebar_email")
        password = st.text_input("Password", type="password", key="sidebar_password")
        
        if st.form_submit_button("Login", type="primary", use_container_width=True):
            if email and password:
                success, message, user, session_token = auth_manager.authenticate_user(
                    email=email,
                    password=password
                )
                
                if success and user and session_token:
                    st.session_state.session_token = session_token
                    st.session_state.user = user.to_dict()
                    st.session_state.login_time = time.time()
                    
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter email and password")
    
    st.sidebar.markdown("---")
    
    # Navigation links
    if st.sidebar.button("📝 Register", use_container_width=True):
        st.switch_page("auth/pages/register.py")
    
    if st.sidebar.button("🔑 Forgot Password", use_container_width=True):
        st.switch_page("auth/pages/reset_password.py")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Demo Accounts")
    st.sidebar.info("""
    **Quick Demo Login:**
    - **Admin:** admin@greenplateai.com / admin123
    - **Kitchen:** kitchen@greenplateai.com / kitchen123
    - **Student:** student@greenplateai.com / student123
    """)


def show_user_sidebar_section(user_info: Dict):
    """Display user information in sidebar."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Profile")
    
    # User avatar and basic info
    col1, col2 = st.sidebar.columns([1, 3])
    
    with col1:
        # Simple avatar (using emoji based on role)
        role = user_info.get('role', 'student')
        avatar_emoji = {
            'admin': '👨‍💼',
            'kitchen_staff': '👨‍🍳',
            'student': '👨‍🎓'
        }.get(role, '👤')
        
        st.sidebar.markdown(f"<h1 style='text-align: center; font-size: 2rem;'>{avatar_emoji}</h1>", unsafe_allow_html=True)
    
    with col2:
        st.sidebar.markdown(f"**{user_info.get('full_name', 'N/A')}**")
        st.sidebar.markdown(f"<small style='color: #666;'>{user_info.get('email', 'N/A')}</small>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<small style='color: #2E8B57;'>{role.title().replace('_', ' ')}</small>", unsafe_allow_html=True)
    
    # Additional user details
    with st.sidebar.expander("📋 More Details", expanded=False):
        if user_info.get('department'):
            st.sidebar.write(f"**Department:** {user_info['department']}")
        
        if user_info.get('phone'):
            st.sidebar.write(f"**Phone:** {user_info['phone']}")
        
        if user_info.get('last_login'):
            last_login = user_info['last_login'][:19]  # Remove microseconds
            st.sidebar.write(f"**Last Login:** {last_login}")
        
        st.sidebar.write(f"**Login Count:** {user_info.get('login_count', 0)}")
        
        if user_info.get('created_at'):
            created_at = user_info['created_at'][:10]  # Just date
            st.sidebar.write(f"**Member Since:** {created_at}")
        
        if user_info.get('is_verified'):
            st.sidebar.success("✅ Email Verified")
        else:
            st.sidebar.warning("⚠️ Email Not Verified")
    
    # Account status
    if user_info.get('is_active'):
        st.sidebar.success("🟢 Account Active")
    else:
        st.sidebar.error("🔴 Account Inactive")


def show_navigation_menu(user_role: UserRole, user_info: Dict):
    """Show role-based navigation menu."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧭 Navigation")
    
    # Define navigation items based on role
    navigation_items = get_navigation_items_for_role(user_role)
    
    # Main navigation
    for item in navigation_items:
        if item.get('type') == 'header':
            st.sidebar.markdown(f"**{item['title']}**")
        elif item.get('type') == 'separator':
            st.sidebar.markdown("---")
        elif item.get('type') == 'item':
            # Check if item is active
            is_active = is_current_page(item.get('page', ''))
            
            if is_active:
                st.sidebar.markdown(f"🎯 **{item['title']}**")
            else:
                if st.sidebar.button(f"{item.get('icon', '📄')} {item['title']}", use_container_width=True, key=f"nav_{item['key']}"):
                    if item.get('page'):
                        st.switch_page(item['page'])
                    elif item.get('action'):
                        execute_navigation_action(item['action'], user_info)
    
    # Role-specific quick access
    show_role_quick_access(user_role, user_info)


def get_navigation_items_for_role(user_role: UserRole) -> List[Dict]:
    """Get navigation items for specific role."""
    
    # Common navigation items
    common_items = [
        {'type': 'item', 'title': 'Dashboard', 'icon': '🏠', 'page': 'app.py', 'key': 'dashboard'},
        {'type': 'separator'},
        {'type': 'header', 'title': 'Main Features'},
    ]
    
    if user_role == UserRole.ADMIN:
        return common_items + [
            {'type': 'item', 'title': 'User Management', 'icon': '👥', 'page': 'pages/admin/users.py', 'key': 'users'},
            {'type': 'item', 'title': 'System Settings', 'icon': '⚙️', 'page': 'pages/admin/settings.py', 'key': 'settings'},
            {'type': 'item', 'title': 'Audit Logs', 'icon': '📋', 'page': 'pages/admin/audit.py', 'key': 'audit'},
            {'type': 'separator'},
            {'type': 'header', 'title': 'Data Management'},
            {'type': 'item', 'title': 'Waste Records', 'icon': '🗑️', 'page': 'pages/waste/records.py', 'key': 'waste_records'},
            {'type': 'item', 'title': 'Inventory', 'icon': '📦', 'page': 'pages/inventory/manage.py', 'key': 'inventory'},
            {'type': 'item', 'title': 'Analytics', 'icon': '📊', 'page': 'pages/analytics/reports.py', 'key': 'analytics'},
            {'type': 'separator'},
            {'type': 'header', 'title': 'AI Features'},
            {'type': 'item', 'title': 'Forecasting', 'icon': '🤖', 'page': 'pages/forecasting/models.py', 'key': 'forecasting'},
            {'type': 'item', 'title': 'Recommendations', 'icon': '💡', 'page': 'pages/recommendations/engine.py', 'key': 'recommendations'},
        ]
    
    elif user_role == UserRole.KITCHEN_STAFF:
        return common_items + [
            {'type': 'item', 'title': 'Inventory Management', 'icon': '📦', 'page': 'pages/kitchen/inventory.py', 'key': 'kitchen_inventory'},
            {'type': 'item', 'title': 'Waste Tracking', 'icon': '🗑️', 'page': 'pages/kitchen/waste.py', 'key': 'kitchen_waste'},
            {'type': 'item', 'title': 'Menu Planning', 'icon': '📋', 'page': 'pages/kitchen/menu.py', 'key': 'menu_planning'},
            {'type': 'separator'},
            {'type': 'header', 'title': 'Reports'},
            {'type': 'item', 'title': 'Daily Reports', 'icon': '📊', 'page': 'pages/kitchen/reports.py', 'key': 'daily_reports'},
            {'type': 'item', 'title': 'Cost Analysis', 'icon': '💰', 'page': 'pages/kitchen/costs.py', 'key': 'cost_analysis'},
            {'type': 'separator'},
            {'type': 'header', 'title': 'AI Features'},
            {'type': 'item', 'title': 'Demand Forecast', 'icon': '🤖', 'page': 'pages/kitchen/forecast.py', 'key': 'demand_forecast'},
            {'type': 'item', 'title': 'Waste Reduction Tips', 'icon': '💡', 'page': 'pages/kitchen/tips.py', 'key': 'waste_tips'},
        ]
    
    else:  # STUDENT
        return common_items + [
            {'type': 'item', 'title': 'My Impact', 'icon': '🌱', 'page': 'pages/student/impact.py', 'key': 'my_impact'},
            {'type': 'item', 'title': 'Waste Tracking', 'icon': '🗑️', 'page': 'pages/student/waste.py', 'key': 'student_waste'},
            {'type': 'item', 'title': 'Sustainability Tips', 'icon': '💡', 'page': 'pages/student/tips.py', 'key': 'sustainability_tips'},
            {'type': 'separator'},
            {'type': 'header', 'title': 'Learning'},
            {'type': 'item', 'title': 'Educational Resources', 'icon': '📚', 'page': 'pages/student/education.py', 'key': 'education'},
            {'type': 'item', 'title': 'Challenges', 'icon': '🏆', 'page': 'pages/student/challenges.py', 'key': 'challenges'},
        ]


def show_role_quick_access(user_role: UserRole, user_info: Dict):
    """Show role-specific quick access section."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Quick Access")
    
    if user_role == UserRole.ADMIN:
        # Admin quick actions
        if st.sidebar.button("👥 Manage Users", use_container_width=True):
            st.switch_page("pages/admin/users.py")
        
        if st.sidebar.button("📊 System Overview", use_container_width=True):
            st.switch_page("pages/admin/overview.py")
        
        if st.sidebar.button("⚙️ Quick Settings", use_container_width=True):
            st.switch_page("pages/admin/quick_settings.py")
    
    elif user_role == UserRole.KITCHEN_STAFF:
        # Kitchen staff quick actions
        if st.sidebar.button("📦 Add Inventory", use_container_width=True):
            st.switch_page("pages/kitchen/add_inventory.py")
        
        if st.sidebar.button("🗑️ Record Waste", use_container_width=True):
            st.switch_page("pages/kitchen/record_waste.py")
        
        if st.sidebar.button("📋 Today's Menu", use_container_width=True):
            st.switch_page("pages/kitchen/today_menu.py")
    
    else:  # STUDENT
        # Student quick actions
        if st.sidebar.button("🌱 Track My Impact", use_container_width=True):
            st.switch_page("pages/student/track_impact.py")
        
        if st.sidebar.button("📊 View Progress", use_container_width=True):
            st.switch_page("pages/student/progress.py")
        
        if st.sidebar.button("💡 Get Tips", use_container_width=True):
            st.switch_page("pages/student/tips.py")


def show_quick_actions_section(user_info: Dict):
    """Show quick actions section."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🚀 Quick Actions")
    
    # Common actions
    if st.sidebar.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    # Profile management
    with st.sidebar.expander("👤 Profile Management", expanded=False):
        if st.button("📝 Edit Profile", use_container_width=True):
            st.switch_page("pages/profile/edit.py")
        
        if st.button("🔑 Change Password", use_container_width=True):
            st.switch_page("pages/profile/change_password.py")
        
        if st.button("📧 Email Settings", use_container_width=True):
            st.switch_page("pages/profile/email_settings.py")
    
    # Notifications
    with st.sidebar.expander("🔔 Notifications", expanded=False):
        if st.button("📬 View All", use_container_width=True):
            st.switch_page("pages/notifications/all.py")
        
        if st.button("⚙️ Notification Settings", use_container_width=True):
            st.switch_page("pages/notifications/settings.py")
    
    # Help and support
    with st.sidebar.expander("❓ Help & Support", expanded=False):
        if st.button("📚 User Guide", use_container_width=True):
            st.switch_page("pages/help/guide.py")
        
        if st.button("🆘 Contact Support", use_container_width=True):
            st.switch_page("pages/help/support.py")
        
        if st.button("📋 FAQ", use_container_width=True):
            st.switch_page("pages/help/faq.py")


def show_sidebar_footer():
    """Show sidebar footer."""
    
    st.sidebar.markdown("---")
    
    # Logout button
    if st.sidebar.button("🚪 Logout", use_container_width=True, type="primary"):
        # Logout user
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
    
    # App info
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8rem;'>
        <strong>GreenPlateAI</strong><br>
        Version 1.0.0<br>
        University Food Waste Management<br>
        <br>
        Made with 🌱 for sustainability
    </div>
    """, unsafe_allow_html=True)


def is_current_page(page_path: str) -> bool:
    """Check if the current page matches the given path."""
    try:
        # Get current page path
        current_page = st.experimental_get_query_params().get('page', [''])[0]
        if not current_page:
            current_page = 'app.py'
        
        # Simple comparison (can be enhanced)
        return current_page == page_path or current_page.endswith(page_path)
    except:
        return False


def execute_navigation_action(action: str, user_info: Dict):
    """Execute navigation action."""
    
    if action == "logout":
        # Logout user
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
        
        st.switch_page("auth/pages/login.py")
    
    elif action == "refresh":
        st.rerun()
    
    elif action == "profile":
        st.switch_page("pages/profile/edit.py")
    
    elif action == "settings":
        user_role = UserRole(user_info.get('role', 'student'))
        if user_role == UserRole.ADMIN:
            st.switch_page("pages/admin/settings.py")
        elif user_role == UserRole.KITCHEN_STAFF:
            st.switch_page("pages/kitchen/settings.py")
        else:
            st.switch_page("pages/student/settings.py")


def show_mobile_navigation():
    """Show mobile-friendly navigation (for small screens)."""
    
    # Check if user is authenticated
    user_info = check_authentication()
    
    if not user_info:
        return
    
    # Mobile navigation header
    st.markdown("---")
    st.markdown("### 📱 Mobile Navigation")
    
    # Quick access buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
    
    with col2:
        if st.button("📊 Dashboard", use_container_width=True):
            st.switch_page("pages/dashboard/main.py")
    
    with col3:
        if st.button("👤 Profile", use_container_width=True):
            st.switch_page("pages/profile/edit.py")
    
    # Role-specific quick actions
    user_role = UserRole(user_info.get('role', 'student'))
    
    if user_role == UserRole.ADMIN:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👥 Users", use_container_width=True):
                st.switch_page("pages/admin/users.py")
        with col2:
            if st.button("⚙️ Settings", use_container_width=True):
                st.switch_page("pages/admin/settings.py")
    
    elif user_role == UserRole.KITCHEN_STAFF:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📦 Inventory", use_container_width=True):
                st.switch_page("pages/kitchen/inventory.py")
        with col2:
            if st.button("🗑️ Waste", use_container_width=True):
                st.switch_page("pages/kitchen/waste.py")
    
    else:  # STUDENT
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🌱 Impact", use_container_width=True):
                st.switch_page("pages/student/impact.py")
        with col2:
            if st.button("💡 Tips", use_container_width=True):
                st.switch_page("pages/student/tips.py")


def show_breadcrumb_navigation():
    """Show breadcrumb navigation for current page."""
    
    user_info = check_authentication()
    if not user_info:
        return
    
    # Get current page info
    current_page = st.experimental_get_query_params().get('page', [''])[0]
    if not current_page:
        current_page = 'Dashboard'
    
    # Create breadcrumb
    breadcrumb_parts = ['🏠 Home']
    
    # Add page-specific breadcrumbs
    if 'admin' in current_page:
        breadcrumb_parts.extend(['Admin', get_page_title(current_page)])
    elif 'kitchen' in current_page:
        breadcrumb_parts.extend(['Kitchen', get_page_title(current_page)])
    elif 'student' in current_page:
        breadcrumb_parts.extend(['Student', get_page_title(current_page)])
    else:
        breadcrumb_parts.append(get_page_title(current_page))
    
    # Display breadcrumb
    breadcrumb_text = ' > '.join(breadcrumb_parts)
    st.markdown(f"<small style='color: #666;'>{breadcrumb_text}</small>", unsafe_allow_html=True)


def get_page_title(page_path: str) -> str:
    """Get page title from path."""
    
    page_titles = {
        'dashboard': 'Dashboard',
        'users': 'User Management',
        'settings': 'Settings',
        'inventory': 'Inventory',
        'waste': 'Waste Tracking',
        'analytics': 'Analytics',
        'forecasting': 'Forecasting',
        'recommendations': 'Recommendations',
        'profile': 'Profile',
        'reports': 'Reports',
        'impact': 'My Impact',
        'tips': 'Tips',
        'education': 'Education',
        'challenges': 'Challenges'
    }
    
    for key, title in page_titles.items():
        if key in page_path.lower():
            return title
    
    return page_path.replace('.py', '').replace('_', ' ').title()


# Main function to be called from main app
def render_sidebar():
    """Main function to render the complete sidebar."""
    
    # Check if user is authenticated
    user_info = check_authentication()
    
    if user_info:
        show_authenticated_sidebar()
    else:
        show_unauthenticated_sidebar()
    
    # Add mobile navigation if needed
    if st.sidebar.button("📱 Mobile Menu", use_container_width=True):
        show_mobile_navigation()
