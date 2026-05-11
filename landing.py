"""
GreenPlateAI Landing Page

A modern, sustainability-focused landing page for the university food waste management platform.
Features hero section, animated metrics, SDG 12 alignment, and investor-ready design.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Page Configuration
st.set_page_config(
    page_title="GreenPlateAI - Eat Smart, Waste Less",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern sustainability theme
st.markdown("""
<style>
/* Global Styles */
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero Section */
.hero-section {
    background: linear-gradient(135deg, #2E8B57 0%, #3CB371 50%, #4ECDC4 100%);
    color: white;
    padding: 4rem 2rem;
    border-radius: 20px;
    margin: 2rem 0;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🌱</text></svg>');
    opacity: 0.1;
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
}

.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    animation: fadeInUp 0.8s ease-out;
}

.hero-tagline {
    font-size: 1.8rem;
    font-weight: 300;
    margin-bottom: 2rem;
    opacity: 0.95;
    animation: fadeInUp 0.8s ease-out 0.2s both;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* KPI Cards */
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border-left: 4px solid #2E8B57;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 100px;
    height: 100px;
    background: linear-gradient(45deg, #2E8B57, #4ECDC4);
    opacity: 0.1;
    border-radius: 0 0 0 100%;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2E8B57;
    margin-bottom: 0.5rem;
    animation: countUp 2s ease-out;
}

@keyframes countUp {
    from { opacity: 0; transform: scale(0.5); }
    to { opacity: 1; transform: scale(1); }
}

.metric-label {
    font-size: 1rem;
    color: #666;
    font-weight: 500;
}

.metric-change {
    font-size: 0.9rem;
    font-weight: 600;
    margin-top: 0.5rem;
}

.positive {
    color: #28a745;
}

.negative {
    color: #dc3545;
}

/* SDG Section */
.sdg-section {
    background: white;
    border-radius: 16px;
    padding: 3rem;
    margin: 2rem 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.sdg-badge {
    background: linear-gradient(45deg, #FF6B6B, #FF8E53);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 25px;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 1rem;
}

/* Benefits Section */
.benefit-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    height: 100%;
}

.benefit-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.12);
}

.benefit-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

/* How It Works */
.process-step {
    text-align: center;
    padding: 2rem;
    position: relative;
}

.process-step::after {
    content: '→';
    position: absolute;
    right: -1rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 2rem;
    color: #2E8B57;
}

.process-step:last-child::after {
    display: none;
}

.step-number {
    background: #2E8B57;
    color: white;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1.5rem;
    margin: 0 auto 1rem;
}

/* CTA Buttons */
.cta-primary {
    background: linear-gradient(45deg, #2E8B57, #3CB371);
    color: white;
    border: none;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    box-shadow: 0 5px 20px rgba(46, 139, 87, 0.3);
}

.cta-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(46, 139, 87, 0.4);
}

.cta-secondary {
    background: white;
    color: #2E8B57;
    border: 2px solid #2E8B57;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: 600;
    font-size: 1.1rem;
    transition: all 0.3s ease;
}

.cta-secondary:hover {
    background: #2E8B57;
    color: white;
}

/* Statistics Section */
.stats-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 16px;
    padding: 3rem;
    margin: 2rem 0;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2.5rem;
    }
    
    .hero-tagline {
        font-size: 1.4rem;
    }
    
    .process-step::after {
        display: none;
    }
    
    .process-step {
        margin-bottom: 2rem;
    }
}

/* Animation Classes */
.fade-in {
    animation: fadeIn 1s ease-out;
}

.slide-in-left {
    animation: slideInLeft 0.8s ease-out;
}

.slide-in-right {
    animation: slideInRight 0.8s ease-out;
}

@keyframes slideInLeft {
    from {
        opacity: 0;
        transform: translateX(-50px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(50px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Custom Streamlit Overrides */
.stButton > button {
    background: linear-gradient(45deg, #2E8B57, #3CB371) !important;
    border: none !important;
    border-radius: 50px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 30px rgba(46, 139, 87, 0.4) !important;
}

.stMetric {
    background: white !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08) !important;
}

/* Footer */
.footer {
    background: #2c3e50;
    color: white;
    padding: 3rem 2rem;
    border-radius: 16px 16px 0 0;
    margin-top: 4rem;
}

/* Testimonial Card */
.testimonial-card {
    background: white;
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    margin: 1rem 0;
    position: relative;
}

.testimonial-card::before {
    content: '"';
    position: absolute;
    top: 1rem;
    left: 1rem;
    font-size: 4rem;
    color: #2E8B57;
    opacity: 0.2;
}
</style>
""", unsafe_allow_html=True)


def create_animated_counter(value, suffix="", duration=2000):
    """Create animated counter for metrics."""
    placeholder = st.empty()
    
    # Simple animation using JavaScript
    animation_js = f"""
    <div id="counter-{id(suffix)}" style="font-size: 2.5rem; font-weight: 700; color: #2E8B57;">0{suffix}</div>
    <script>
    function animateCounter(element, start, end, duration) {{
        let startTimestamp = null;
        const step = (timestamp) => {{
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const current = Math.floor(progress * end);
            element.textContent = current + "{suffix}";
            if (progress < 1) {{
                window.requestAnimationFrame(step);
            }}
        }};
        window.requestAnimationFrame(step);
    }}
    
    const counter = document.getElementById('counter-{id(suffix)}');
    if (counter) {{
        animateCounter(counter, 0, {value}, {duration});
    }}
    </script>
    """
    
    placeholder.markdown(animation_js, unsafe_allow_html=True)


def create_animated_gauge_chart(value, title, max_value=100, color="#2E8B57"):
    """Create animated gauge chart."""
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title},
        delta = {'reference': max_value * 0.8},
        gauge = {
            'axis': {'range': [None, max_value]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, max_value * 0.5], 'color': "lightgray"},
                {'range': [max_value * 0.5, max_value], 'color': color}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': max_value * 0.9
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        font={'color': "#2c3e50"},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=0, l=0, r=0)
    )
    
    return fig


def create_animated_bar_chart(data, title, color="#2E8B57"):
    """Create animated bar chart."""
    fig = px.bar(
        data, 
        x=data.columns[0], 
        y=data.columns[1],
        color_discrete_sequence=[color],
        title=title
    )
    
    fig.update_layout(
        height=300,
        font={'color': "#2c3e50"},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=0, l=0, r=0),
        showlegend=False
    )
    
    fig.update_traces(marker_line_width=0)
    
    return fig


def show_hero_section():
    """Display hero section with tagline."""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">GreenPlateAI</h1>
        <p class="hero-tagline">Eat Smart, Waste Less</p>
        <p style="font-size: 1.2rem; opacity: 0.9; max-width: 600px; margin: 0 auto;">
            Transforming university food service with AI-powered waste reduction. 
            Join us in creating a sustainable future, one plate at a time.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🚀 Start Free Trial", use_container_width=True, key="hero_trial"):
            st.info("Sign up for your free 30-day trial!")
    
    with col2:
        if st.button("📅 Book Demo", use_container_width=True, key="hero_demo"):
            st.info("Schedule a personalized demo!")
    
    with col3:
        if st.button("📊 View Impact", use_container_width=True, key="hero_impact"):
            st.info("See our environmental impact!")


def show_animated_metrics():
    """Display animated KPI metrics."""
    st.markdown("## 📊 Real-Time Impact Metrics")
    
    # Create animated data
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">2,847</div>
            <div class="metric-label">Kg Food Saved</div>
            <div class="metric-change positive">↑ 23% this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">$14,235</div>
            <div class="metric-label">Cost Savings</div>
            <div class="metric-change positive">↑ 18% this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">5,678</div>
            <div class="metric-label">CO₂ kg Reduced</div>
            <div class="metric-change positive">↑ 31% this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">234</div>
            <div class="metric-label">Partner Universities</div>
            <div class="metric-change positive">↑ 12 this month</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Animated charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Waste reduction trend
        waste_data = pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Waste_Reduced_kg': [450, 680, 890, 1200, 1450, 1780]
        })
        
        fig = create_animated_bar_chart(waste_data, "Monthly Waste Reduction (kg)")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Efficiency gauge
        fig = create_animated_gauge_chart(87, "System Efficiency (%)")
        st.plotly_chart(fig, use_container_width=True)


def show_sdg_section():
    """Display SDG 12 sustainability section."""
    st.markdown("""
    <div class="sdg-section">
        <div class="sdg-badge">SDG 12: Responsible Consumption & Production</div>
        <h2 style="color: #2c3e50; margin-bottom: 1rem;">🌍 Aligned with Global Sustainability Goals</h2>
        <p style="color: #666; font-size: 1.1rem; line-height: 1.6;">
            GreenPlateAI directly supports UN Sustainable Development Goal 12 by promoting 
            responsible consumption and production patterns in university food services. 
            Our AI-powered platform helps institutions reduce food waste, minimize environmental impact, 
            and create sustainable food systems for future generations.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # SDG Impact Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">🎯</div>
            <h3>Target 12.3</h3>
            <p>Halving per capita global food waste at retail and consumer levels by 2030</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">📈</div>
            <h3>Measurable Impact</h3>
            <p>Track and report on food waste reduction with real-time analytics and reporting</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="benefit-card">
            <div class="benefit-icon">🤝</div>
            <h3>Partnership Building</h3>
            <p>Collaborate with universities worldwide to achieve sustainable food systems</p>
        </div>
        """, unsafe_allow_html=True)


def show_statistics():
    """Display food waste and CO2 reduction statistics."""
    st.markdown("## 📈 Environmental Impact Statistics")
    
    # Create comprehensive statistics section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="stats-section">
            <h2 style="margin-bottom: 2rem;">🌱 Food Waste Reduction</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">40%</h3>
                    <p>Average Waste Reduction</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">2.8M</h3>
                    <p>Kg Food Saved Annually</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">1.2M</h3>
                    <p>Meals Saved from Waste</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">$6.5M</h3>
                    <p>Cost Savings Achieved</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stats-section">
            <h2 style="margin-bottom: 2rem;">🌍 CO₂ Reduction Impact</h2>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">5.6M</h3>
                    <p>Kg CO₂ Reduced</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">1.4M</h3>
                    <p>Trees Equivalent</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">284K</h3>
                    <p>Gallons Water Saved</p>
                </div>
                <div style="text-align: center;">
                    <h3 style="font-size: 2rem; margin: 0;">350</h3>
                    <p>Cars Off Road Annually</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Impact visualization
    st.markdown("### 📊 Cumulative Impact Over Time")
    
    # Create time series data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    food_waste = [100, 180, 290, 450, 680, 890, 1200, 1450, 1780, 2100, 2450, 2847]
    co2_reduction = [200, 360, 580, 900, 1360, 1780, 2400, 2900, 3560, 4200, 4900, 5600, 5678]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Food Waste Reduction (kg)', 'CO₂ Reduction (kg)'),
        vertical_spacing=0.1
    )
    
    fig.add_trace(
        go.Scatter(x=months, y=food_waste, mode='lines+markers', 
                  line=dict(color='#2E8B57', width=3), name='Food Waste'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=months, y=co2_reduction, mode='lines+markers',
                  line=dict(color='#FF6B6B', width=3), name='CO₂'),
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        font={'color': "#2c3e50"},
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=50, b=0, l=0, r=0),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_benefits():
    """Display benefits section."""
    st.markdown("## 💼 Benefits for Universities")
    
    col1, col2, col3 = st.columns(3)
    
    benefits = [
        {
            "icon": "💰",
            "title": "Cost Savings",
            "description": "Reduce food costs by up to 40% through optimized purchasing and waste reduction strategies."
        },
        {
            "icon": "🌱",
            "title": "Sustainability",
            "description": "Meet environmental goals and enhance your institution's sustainability reputation."
        },
        {
            "icon": "📊",
            "title": "Data Insights",
            "description": "Get actionable insights with AI-powered analytics and real-time waste tracking."
        },
        {
            "icon": "🎓",
            "title": "Educational Value",
            "description": "Engage students in sustainability initiatives and provide hands-on learning experiences."
        },
        {
            "icon": "🏆",
            "title": "Compliance",
            "description": "Meet regulatory requirements and achieve sustainability certifications."
        },
        {
            "icon": "🤝",
            "title": "Community Impact",
            "description": "Contribute to local food security and community well-being programs."
        }
    ]
    
    for i, benefit in enumerate(benefits):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
            <div class="benefit-card fade-in">
                <div class="benefit-icon">{benefit['icon']}</div>
                <h3>{benefit['title']}</h3>
                <p>{benefit['description']}</p>
            </div>
            """, unsafe_allow_html=True)


def show_how_it_works():
    """Display how it works section."""
    st.markdown("## 🔄 How GreenPlateAI Works")
    
    steps = [
        {
            "number": "1",
            "title": "Data Collection",
            "description": "AI-powered sensors and manual tracking collect real-time food waste data from dining halls."
        },
        {
            "number": "2", 
            "title": "AI Analysis",
            "description": "Machine learning algorithms analyze patterns, identify waste hotspots, and predict future waste."
        },
        {
            "number": "3",
            "title": "Smart Recommendations",
            "description": "Get actionable insights for menu planning, portion control, and inventory management."
        },
        {
            "number": "4",
            "title": "Continuous Improvement",
            "description": "Track progress, measure impact, and continuously optimize your food service operations."
        }
    ]
    
    # Create process steps
    for i, step in enumerate(steps):
        col = st.columns(4)[i % 4]
        with col:
            st.markdown(f"""
            <div class="process-step slide-in-left">
                <div class="step-number">{step['number']}</div>
                <h3>{step['title']}</h3>
                <p>{step['description']}</p>
            </div>
            """, unsafe_allow_html=True)


def show_testimonials():
    """Display testimonials section."""
    st.markdown("## 💬 What Our Partners Say")
    
    testimonials = [
        {
            "name": "Dr. Sarah Johnson",
            "title": "Director of Sustainability, State University",
            "content": "GreenPlateAI has transformed our food service operations. We've reduced waste by 45% and saved over $200,000 annually."
        },
        {
            "name": "Michael Chen",
            "title": "Food Service Manager, Tech University",
            "content": "The AI insights are incredible. We can now predict demand and adjust our menus accordingly. It's been a game-changer."
        },
        {
            "name": "Prof. Emily Rodriguez",
            "title": "Environmental Science Director, Green Valley College",
            "content": "Our students love the sustainability aspect. GreenPlateAI has become a cornerstone of our campus sustainability program."
        }
    ]
    
    for testimonial in testimonials:
        st.markdown(f"""
        <div class="testimonial-card">
            <p>"{testimonial['content']}"</p>
            <p style="font-weight: 600; color: #2E8B57; margin-top: 1rem;">
                - {testimonial['name']}<br>
                <small style="color: #666;">{testimonial['title']}</small>
            </p>
        </div>
        """, unsafe_allow_html=True)


def show_partners():
    """Display partner universities section."""
    st.markdown("## 🎓 Trusted by Leading Universities")
    
    partners = [
        "State University", "Tech Institute", "Green Valley College", 
        "Metro University", "Science Academy", "Liberal Arts College"
    ]
    
    # Create partner logos (using text placeholders)
    cols = st.columns(3)
    for i, partner in enumerate(partners):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; background: white; border-radius: 8px; margin: 0.5rem 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <div style="font-size: 1.2rem; font-weight: 600; color: #2c3e50;">{partner}</div>
                <div style="font-size: 0.9rem; color: #666; margin-top: 0.5rem;">Partner Since 2023</div>
            </div>
            """, unsafe_allow_html=True)


def show_cta_section():
    """Display call-to-action section."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 4rem 2rem; border-radius: 16px; text-align: center; margin: 2rem 0;">
        <h2 style="font-size: 2.5rem; margin-bottom: 1rem;">Ready to Transform Your Food Service?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Join hundreds of universities already using GreenPlateAI to reduce waste, 
            save money, and achieve their sustainability goals.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start Free Trial", use_container_width=True, key="cta_trial"):
            st.info("Start your 30-day free trial today!")
    
    with col2:
        if st.button("📅 Schedule Demo", use_container_width=True, key="cta_demo"):
            st.info("Book a personalized demo with our team!")
    
    with col3:
        if st.button("📞 Contact Sales", use_container_width=True, key="cta_sales"):
            st.info("Talk to our sales team!")


def show_footer():
    """Display footer."""
    st.markdown("""
    <div class="footer">
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 2rem; margin-bottom: 2rem;">
            <div>
                <h3 style="color: white; margin-bottom: 1rem;">🥗 GreenPlateAI</h3>
                <p style="color: #bdc3c7; line-height: 1.6;">
                    Transforming university food service with AI-powered waste reduction. 
                    Eat Smart, Waste Less.
                </p>
            </div>
            <div>
                <h4 style="color: white; margin-bottom: 1rem;">Product</h4>
                <ul style="color: #bdc3c7; list-style: none; padding: 0;">
                    <li style="margin-bottom: 0.5rem;">Features</li>
                    <li style="margin-bottom: 0.5rem;">Pricing</li>
                    <li style="margin-bottom: 0.5rem;">Case Studies</li>
                    <li style="margin-bottom: 0.5rem;">API Docs</li>
                </ul>
            </div>
            <div>
                <h4 style="color: white; margin-bottom: 1rem;">Company</h4>
                <ul style="color: #bdc3c7; list-style: none; padding: 0;">
                    <li style="margin-bottom: 0.5rem;">About Us</li>
                    <li style="margin-bottom: 0.5rem;">Careers</li>
                    <li style="margin-bottom: 0.5rem;">Blog</li>
                    <li style="margin-bottom: 0.5rem;">Contact</li>
                </ul>
            </div>
            <div>
                <h4 style="color: white; margin-bottom: 1rem;">Connect</h4>
                <ul style="color: #bdc3c7; list-style: none; padding: 0;">
                    <li style="margin-bottom: 0.5rem;">Twitter</li>
                    <li style="margin-bottom: 0.5rem;">LinkedIn</li>
                    <li style="margin-bottom: 0.5rem;">GitHub</li>
                    <li style="margin-bottom: 0.5rem;">Email</li>
                </ul>
            </div>
        </div>
        
        <div style="border-top: 1px solid #34495e; padding-top: 2rem; text-align: center; color: #bdc3c7;">
            <p>&copy; 2024 GreenPlateAI. All rights reserved. | 
            <a href="#" style="color: #3498db;">Privacy Policy</a> | 
            <a href="#" style="color: #3498db;">Terms of Service</a> | 
            <a href="#" style="color: #3498db;">Cookie Policy</a></p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main landing page function."""
    
    # Hero Section
    show_hero_section()
    
    # Animated Metrics
    show_animated_metrics()
    
    # SDG Section
    show_sdg_section()
    
    # Statistics
    show_statistics()
    
    # Benefits
    show_benefits()
    
    # How It Works
    show_how_it_works()
    
    # Testimonials
    show_testimonials()
    
    # Partners
    show_partners()
    
    # CTA Section
    show_cta_section()
    
    # Footer
    show_footer()


if __name__ == "__main__":
    main()
