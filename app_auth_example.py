"""
Example main application demonstrating GreenPlateAI authentication system.
This file shows how to integrate the authentication system into a Streamlit app
with role-based access control and protected pages.
"""

import streamlit as st
import time
# Import authentication components
from auth import (
    auth_manager, check_authentication, get_current_user, is_authenticated,
    require_auth, require_admin, require_kitchen_staff,
    show_authenticated_sidebar, render_sidebar
)
from models.user_auth import UserRole


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="GreenPlateAI - Food Waste Management",
        page_icon="🥗",
        initial_sidebar_state="expanded"
    )
    
    # Check authentication and show appropriate content
    if not is_authenticated():
        show_login_page()
    else:
        show_main_app()

def show_login_page():
    """Show login page for unauthenticated users."""
    # Import login page
    from auth.pages.login import show_login_page as login_page
    login_page()

def show_main_app():
    """Show main application for authenticated users."""
    # Get current user
    user_info = get_current_user()
    user_role = UserRole(user_info.get('role', 'student'))
    
    # Show sidebar navigation
    render_sidebar()
    
    # Main content area
    st.markdown("# 🥗 GreenPlateAI Dashboard")
    st.markdown(f"Welcome back, **{user_info.get('full_name', user_info.get('username'))}**!")
    
    # Role-based dashboard
    if user_role == UserRole.ADMIN:
        show_admin_dashboard()
    elif user_role == UserRole.KITCHEN_STAFF:
        show_kitchen_staff_dashboard()
    else:  # STUDENT
        show_student_dashboard()


@require_auth
def show_admin_dashboard():
    """Admin dashboard with full system access."""
    st.markdown("## 👨‍💼 Administrator Dashboard")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", "156", "+12 this week")
    
    with col2:
        st.metric("Active Sessions", "23", "-3 from yesterday")
    
    with col3:
        st.metric("System Health", "98%", "Optimal")
    
    with col4:
        st.metric("Data Points", "1,234", "+234 today")
    
    st.markdown("---")
    
    # Admin-specific features
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Users", "⚙️ Settings", "📊 Analytics", "🔒 Security"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        show_system_settings()
    
    with tab3:
        show_system_analytics()
    
    with tab4:
        show_security_management()


@require_kitchen_staff
def show_kitchen_staff_dashboard():
    """Kitchen staff dashboard with kitchen management features."""
    
    st.markdown("## 👨‍🍳 Kitchen Staff Dashboard")
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Today's Waste", "45.2 kg", "-12% from average")
    
    with col2:
        st.metric("Inventory Level", "78%", "Optimal")
    
    with col3:
        st.metric("Cost Savings", "$234", "+$45 this week")
    
    st.markdown("---")
    
    # Kitchen-specific features
    tab1, tab2, tab3 = st.tabs(["📦 Inventory", "🗑️ Waste Tracking", "📋 Menu Planning"])
    
    with tab1:
        show_inventory_management()
    
    with tab2:
        show_waste_tracking()
    
    with tab3:
        show_menu_planning()


def show_student_dashboard():
    """Student dashboard with personal tracking features."""
    
    st.markdown("## 👨‍🎓 Student Dashboard")
    
    # Personal stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("My Impact", "-12.5 kg", "Great progress!")
    
    with col2:
        st.metric("Eco Score", "85/100", "+5 this week")
    
    with col3:
        st.metric("Rank", "#23", "Top 10%")
    
    st.markdown("---")
    
    # Student-specific features
    tab1, tab2, tab3 = st.tabs(["🌱 My Impact", "💡 Tips", "🏆 Challenges"])
    
    with tab1:
        show_personal_impact()
    
    with tab2:
        show_sustainability_tips()
    
    with tab3:
        show_challenges()


# Feature demonstration functions
def show_user_management():
    """Show user management interface (admin only)."""
    
    st.markdown("### User Management")
    
    # Add new user form
    with st.expander("➕ Add New User", expanded=False):
        with st.form("add_user_form"):
            email = st.text_input("Email")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["student", "kitchen_staff", "admin"])
            
            if st.form_submit_button("Add User"):
                if email and full_name:
                    success, message, user = auth_manager.register_user(
                        email=email,
                        username=email.split('@')[0],
                        password="temp123",
                        full_name=full_name,
                        role=UserRole(role)
                    )
                    
                    if success:
                        st.success(f"✅ User created: {full_name}")
                    else:
                        st.error(f"❌ Error: {message}")
    
    # User list (mock data)
    users = [
        {"name": "John Doe", "email": "john@university.edu", "role": "student", "status": "Active"},
        {"name": "Jane Smith", "email": "jane@university.edu", "role": "kitchen_staff", "status": "Active"},
        {"name": "Admin User", "email": "admin@greenplateai.com", "role": "admin", "status": "Active"},
    ]
    
    st.dataframe(users, use_container_width=True)


def show_inventory_management():
    """Show inventory management (kitchen staff only)."""
    
    st.markdown("### Current Inventory")
    
    # Mock inventory data
    inventory = [
        {"item": "Rice", "quantity": "150 kg", "status": "Good", "last_updated": "2 hours ago"},
        {"item": "Chicken", "quantity": "75 kg", "status": "Low", "last_updated": "1 hour ago"},
        {"item": "Vegetables", "quantity": "100 kg", "status": "Good", "last_updated": "3 hours ago"},
    ]
    
    st.dataframe(inventory, use_container_width=True)
    
    # Quick actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 Add Inventory", use_container_width=True):
            st.info("Add inventory feature coming soon!")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Inventory report feature coming soon!")


def show_personal_impact():
    """Show personal impact tracking (students only)."""
    
    st.markdown("### Your Environmental Impact")
    
    # Mock personal data
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Food Saved", "23.5 kg", "This month")
        st.metric("CO₂ Reduced", "58.75 kg", "This month")
        st.metric("Water Saved", "4,700 L", "This month")
    
    with col2:
        st.metric("Money Saved", "$117.50", "This month")
        st.metric("Trees Equivalent", "2.3", "This month")
        st.metric("Rank", "#23 / 1,234", "University")
    
    # Progress chart (placeholder)
    st.markdown("### 📈 Your Progress")
    st.info("Progress tracking charts coming soon!")


# Protected page examples
@require_admin
def admin_only_page():
    """Example of admin-only page."""
    st.markdown("# 🔒 Admin Only Page")
    st.success("✅ You have admin access!")
    st.info("This page is only visible to administrators.")


@require_kitchen_staff
def kitchen_staff_only_page():
    """Example of kitchen staff only page."""
    st.markdown("# 👨‍🍳 Kitchen Staff Only Page")
    st.success("✅ You have kitchen staff access!")
    st.info("This page is only visible to kitchen staff and administrators.")


# Example of how to use decorators in other pages
@require_auth
def protected_page_example():
    """Example of protected page."""
    st.markdown("# 🔐 Protected Page")
    
    user_info = get_current_user()
    st.write(f"Hello, {user_info.get('full_name', 'User')}!")
    
    # Check specific permissions
    from models.user_auth import User
    temp_user = User()
    temp_user.role = UserRole(user_info.get('role', 'student'))
    
    if temp_user.has_permission('manage_users'):
        st.success("You can manage users")
    else:
        st.info("You cannot manage users")


# Additional utility functions
def show_logout_button():
    """Show logout button in main app."""
    if st.button("🚪 Logout", use_container_width=True):
        from auth.pages.login import logout_user
        logout_user()


# Main execution
if __name__ == "__main__":
    main()
