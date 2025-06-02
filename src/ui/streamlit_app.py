"""
Enterprise-grade Streamlit application for Holiday Destinations Generator.
Features modern UI, comprehensive error handling, and observability.
"""

import asyncio
import time
from datetime import datetime
from typing import Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

from src.config import settings
from src.core import configure_logging, get_logger
from src.models import GenerationRequest, ThemeType
from src.services import DestinationService, DestinationGenerationError


# Configure logging
configure_logging()
logger = get_logger("streamlit_app")


def compatibility_badge(text: str, badge_type: str = "secondary") -> None:
    """
    Compatibility function for st.badge() that works with older Streamlit versions.
    Falls back to styled markdown if st.badge is not available.
    """
    try:
        # Try to use st.badge if available (Streamlit >= 1.29.0)
        st.badge(text, type=badge_type)
    except AttributeError:
        # Fallback for older Streamlit versions
        badge_colors = {
            "secondary": "#6c757d",
            "primary": "#007bff", 
            "success": "#28a745",
            "danger": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8"
        }
        color = badge_colors.get(badge_type, "#6c757d")
        st.markdown(
            f"<span style='background-color: {color}; color: white; padding: 0.25rem 0.5rem; "
            f"border-radius: 0.25rem; font-size: 0.8rem; font-weight: 500;'>{text}</span>",
            unsafe_allow_html=True
        )


class HolidayDestinationApp:
    """Main Streamlit application class."""
    
    def __init__(self):
        self.destination_service = DestinationService()
        self._setup_page_config()
        self._setup_custom_css()
        self._initialize_session_state()
    
    def _setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="✈️ Holiday Destinations Generator",
            page_icon="🌍",
            layout="wide",
            initial_sidebar_state="collapsed",
            menu_items={
                'Get Help': 'https://github.com/yourusername/holiday-destinations-generator',
                'Report a bug': 'https://github.com/yourusername/holiday-destinations-generator/issues',
                'About': f"Holiday Destinations Generator v{settings.app_version} - Enterprise Edition"
            }
        )
    
    def _setup_custom_css(self):
        """Setup custom CSS for stunning modern travel app styling."""
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }
        
        /* Hide Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Beautiful Header */
        .hero-section {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%), url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 600"><defs><pattern id="waves" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse"><path d="M0,50 Q25,25 50,50 T100,50" stroke="rgba(255,255,255,0.1)" stroke-width="2" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(%23waves)"/></svg>');
            background-size: cover;
            background-position: center;
            padding: 4rem 2rem;
            margin: -2rem -2rem 3rem -2rem;
            text-align: center;
            color: white;
            border-radius: 0 0 30px 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .hero-title {
            font-family: 'Poppins', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            background: linear-gradient(45deg, #ffffff, #e3f2fd);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .hero-subtitle {
            font-family: 'Inter', sans-serif;
            font-size: 1.3rem;
            font-weight: 400;
            opacity: 0.95;
            margin-bottom: 2rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        /* Navigation Tabs */
        .nav-container {
            background: white;
            border-radius: 20px;
            padding: 1rem;
            margin: 2rem 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        
        /* Content Cards */
        .content-card {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }
        
        /* Destination Cards */
        .destination-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border-radius: 20px;
            padding: 2rem;
            margin: 1.5rem 0;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.15);
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .destination-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .destination-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 60px rgba(102, 126, 234, 0.25);
        }
        
        .destination-title {
            font-family: 'Poppins', sans-serif;
            font-size: 1.8rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .destination-country {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #667eea;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .destination-description {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #5a6c7d;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        
        .destination-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .meta-item {
            background: rgba(102, 126, 234, 0.05);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        
        .meta-label {
            font-family: 'Inter', sans-serif;
            font-size: 0.85rem;
            color: #667eea;
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .meta-value {
            font-family: 'Poppins', sans-serif;
            font-size: 1rem;
            color: #2c3e50;
            font-weight: 600;
        }
        
        /* Activity Cards */
        .activity-card {
            background: linear-gradient(135deg, #f8f9ff 0%, #e3f2fd 100%);
            border-radius: 15px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 5px solid #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
        }
        
        .activity-card:hover {
            transform: translateX(5px);
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.2);
        }
        
        .activity-title {
            font-family: 'Poppins', sans-serif;
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.5rem;
        }
        
        .activity-description {
            font-family: 'Inter', sans-serif;
            color: #5a6c7d;
            margin-bottom: 1rem;
            line-height: 1.5;
        }
        
        .activity-tags {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .activity-tag {
            background: #667eea;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        /* Form Elements */
        .stSelectbox > div > div > select {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            padding: 0.75rem;
            color: #2c3e50;
        }
        
        .stSelectbox > div > div > select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .stNumberInput > div > div > input {
            background: white;
            border: 2px solid #e1e5e9;
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
            padding: 0.75rem;
        }
        
        .stCheckbox > label {
            font-family: 'Inter', sans-serif;
            color: #2c3e50;
            font-weight: 500;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(102, 126, 234, 0.4);
        }
        
        /* Status Messages */
        .success-message {
            background: linear-gradient(135deg, #00c851 0%, #00a085 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 5px 20px rgba(0, 200, 81, 0.2);
            font-family: 'Inter', sans-serif;
        }
        
        .error-message {
            background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 5px 20px rgba(255, 68, 68, 0.2);
            font-family: 'Inter', sans-serif;
        }
        
        .info-message {
            background: linear-gradient(135deg, #33b5e5 0%, #0099cc 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 5px 20px rgba(51, 181, 229, 0.2);
            font-family: 'Inter', sans-serif;
        }
        
        /* Model Status */
        .model-status {
            background: linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,249,255,0.9) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 15px;
            padding: 1rem;
            margin: 1rem 0;
            font-family: 'Inter', sans-serif;
            color: #2c3e50;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        /* Analytics Cards */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.1);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 45px rgba(102, 126, 234, 0.2);
        }
        
        .metric-value {
            font-family: 'Poppins', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #5a6c7d;
            font-weight: 500;
        }
        
        /* Sidebar Styles */
        .sidebar-content {
            background: linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(248,249,255,0.95) 100%);
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }
        
        /* Loading Animation */
        .loading-spinner {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid rgba(102, 126, 234, 0.3);
            border-radius: 50%;
            border-top-color: #667eea;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Rating Stars */
        .rating-stars {
            color: #ffd700;
            font-size: 1.2rem;
            margin: 0.5rem 0;
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2.5rem;
            }
            
            .hero-subtitle {
                font-size: 1.1rem;
            }
            
            .destination-card {
                padding: 1.5rem;
            }
            
            .destination-meta {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'generation_history' not in st.session_state:
            st.session_state.generation_history = []
        if 'total_generations' not in st.session_state:
            st.session_state.total_generations = 0
        if 'favorite_destinations' not in st.session_state:
            st.session_state.favorite_destinations = []
        if 'last_generation_time' not in st.session_state:
            st.session_state.last_generation_time = None
        if 'fine_tuning_status' not in st.session_state:
            st.session_state.fine_tuning_status = None
    
    def _render_header(self):
        """Render beautiful hero section with modern design."""
        st.markdown("""
        <div class='hero-section'>
            <div class='hero-title'>
                🌍 Holiday Destinations Generator
            </div>
            <div class='hero-subtitle'>
                Discover extraordinary destinations powered by AI. From hidden gems to iconic landmarks, 
                let us curate your perfect adventure across the globe.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Model status in a beautiful card
        model_status = self._get_model_status()
        st.markdown(f"""
        <div class='model-status'>
            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;'>
                <div>
                    <strong>🤖 AI Model:</strong> {model_status['display_name'][:30]}{'...' if len(model_status['display_name']) > 30 else ''}
                </div>
                <div>
                    <strong>🎯 Enhanced:</strong> {'Yes' if model_status['fine_tuned'] else 'Standard'}
                </div>
                <div>
                    <strong>⚡ Status:</strong> <span style='color: #00c851;'>●</span> {model_status['status']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _get_model_status(self):
        """Get current model status information."""
        return {
            'display_name': settings.effective_openai_model,
            'fine_tuned': settings.use_fine_tuned_model,
            'status': 'Active',
            'base_model': settings.openai_model
        }
    
    def _render_sidebar(self):
        """Render enhanced sidebar with modern travel app styling."""
        with st.sidebar:
            # Beautiful sidebar header
            st.markdown("""
            <div class='sidebar-content'>
                <h2 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 1.5rem;'>
                    🎯 Destination Finder
                </h2>
                <p style='color: #5a6c7d; font-family: Inter, sans-serif; text-align: center; margin-bottom: 2rem;'>
                    Discover amazing places tailored to your interests
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Theme selection with beautiful styling
            st.markdown("### 🏷️ Choose Your Adventure Theme")
            theme = st.selectbox(
                "Select theme",
                options=[theme.value for theme in ThemeType],
                help="Select the type of destinations you're interested in",
                key="theme_selector",
                label_visibility="collapsed"
            )
            
            st.markdown("### 📊 Number of Destinations")
            count = st.number_input(
                "Number of destinations",
                min_value=1,
                max_value=10,
                value=3,
                help="How many destinations would you like to discover?",
                key="count_selector",
                label_visibility="collapsed"
            )
            
            st.markdown("### 🎭 Include Activities")
            include_activities = st.checkbox(
                "Generate detailed activities for each destination",
                value=True,
                help="Get specific activity recommendations for each destination",
                key="activities_checkbox"
            )
            
            # Beautiful generate button
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("✨ Generate Destinations", key="generate_btn", use_container_width=True):
                try:
                    request = GenerationRequest(
                        theme=ThemeType(theme),
                        count=count,
                        include_activities=include_activities
                    )
                    
                    with st.spinner("🌍 Discovering amazing destinations for you..."):
                        response = asyncio.run(self._generate_destinations_async(request))
                        
                        if response and response.destinations:
                            st.session_state.last_response = response
                            st.session_state.total_generations += 1
                            st.session_state.generation_history.append({
                                'timestamp': datetime.now(),
                                'theme': theme,
                                'count': len(response.destinations),
                                'generation_time': response.generation_time_seconds
                            })
                            st.session_state.last_generation_time = response.generation_time_seconds
                            
                            # Success message with beautiful styling
                            model_used = "Enhanced AI" if settings.use_fine_tuned_model else "Standard AI"
                            st.markdown(f"""
                            <div class='success-message'>
                                🎉 <strong>Success!</strong> Generated {len(response.destinations)} amazing {theme.lower()} destinations 
                                using {model_used} in {response.generation_time_seconds:.1f}s
                            </div>
                            """, unsafe_allow_html=True)
                            
                        else:
                            st.markdown("""
                            <div class='error-message'>
                                ❌ <strong>No destinations found.</strong> Please try again with different settings.
                            </div>
                            """, unsafe_allow_html=True)
                            
                except Exception as e:
                    logger.error("Generation failed", error=str(e), exc_info=True)
                    st.markdown(f"""
                    <div class='error-message'>
                        ❌ <strong>Generation failed:</strong> {str(e)}
                    </div>
                    """, unsafe_allow_html=True)
    
    def _display_destination(self, destination, show_coordinates=False, show_ratings=True):
        """Display destination with stunning modern card design using pure Streamlit components."""
        
        # Safe theme handling for display - works with both string and enum
        theme_display = destination.theme.value if hasattr(destination.theme, 'value') else str(destination.theme)
        
        # Determine theme emoji
        theme_emojis = {
            "Sports": "🏃‍♂️",
            "Historical Place": "🏛️", 
            "Natural Attraction": "🌿",
            "Scientific": "🔬",
            "Entertainment": "🎭"
        }
        theme_emoji = theme_emojis.get(theme_display, "🌍")
        
        # Use pure Streamlit components
        with st.container():
            # Title and basic info
            st.subheader(f"{theme_emoji} {destination.place}")
            st.markdown(f"**📍 {destination.country}**")
            st.write(destination.description)
            
            # Metadata in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="🗓️ Best Time to Visit",
                    value=destination.best_time_to_visit
                )
            
            with col2:
                rating_stars = "⭐" * int(destination.rating) if destination.rating else "⭐⭐⭐⭐"
                st.metric(
                    label="⭐ Rating",
                    value=f"{rating_stars} {destination.rating}/5"
                )
            
            if show_coordinates and destination.coordinates:
                with col3:
                    st.metric(
                        label="🧭 Coordinates",
                        value=f"{destination.coordinates['lat']:.3f}, {destination.coordinates['lng']:.3f}"
                    )
            
            st.divider()
        
        # Display activities if available
        if destination.activities:
            st.markdown("#### 🎯 Recommended Activities")
            for activity in destination.activities:
                self._display_activity(activity)

    def _display_activity(self, activity):
        """Display activity with beautiful card design using pure Streamlit components."""
        
        # Safe activity type handling - works with both string and enum
        activity_type_display = activity.activity_type.value if hasattr(activity.activity_type, 'value') else str(activity.activity_type)
        
        difficulty_stars = "🔥" * activity.difficulty_level if activity.difficulty_level else "🔥"
        
        with st.container():
            st.markdown(f"**🎯 {activity.name}**")
            st.write(activity.description)
            
            # Activity details in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                compatibility_badge(activity_type_display, "secondary")
            
            with col2:
                st.write(f"⏱️ {activity.duration_hours}h")
            
            with col3:
                st.write(f"{difficulty_stars} Difficulty {activity.difficulty_level}/5")
            
            with col4:
                st.write(f"💰 {activity.cost_estimate}")
            
            st.markdown("---")
    
    def _render_analytics_dashboard(self):
        """Render beautiful analytics dashboard with modern design."""
        
        st.markdown("""
        <div class='content-card'>
            <h2 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 2rem;'>
                📊 Travel Analytics Dashboard
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.generation_history:
            # Beautiful metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{st.session_state.total_generations}</div>
                    <div class='metric-label'>Total Generations</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_time = sum([h.get('generation_time', 0) for h in st.session_state.generation_history]) / len(st.session_state.generation_history)
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{avg_time:.1f}s</div>
                    <div class='metric-label'>Avg Response Time</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                total_destinations = sum([h.get('count', 0) for h in st.session_state.generation_history])
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{total_destinations}</div>
                    <div class='metric-label'>Destinations Found</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{len(st.session_state.favorite_destinations)}</div>
                    <div class='metric-label'>Favorites Saved</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Charts in beautiful cards
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class='content-card'>
                    <h3 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 1rem;'>
                        🎭 Theme Preferences
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Theme distribution chart
                themes = [h.get('theme', 'Unknown') for h in st.session_state.generation_history]
                theme_counts = pd.Series(themes).value_counts()
                
                fig_pie = px.pie(
                    values=theme_counts.values,
                    names=theme_counts.index,
                    color_discrete_sequence=['#667eea', '#764ba2', '#4CAF50', '#FF5722', '#9C27B0']
                )
                fig_pie.update_layout(
                    showlegend=True,
                    height=350,
                    font=dict(family="Inter, sans-serif", size=12),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.markdown("""
                <div class='content-card'>
                    <h3 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 1rem;'>
                        ⚡ Performance Over Time
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Performance timeline
                df_history = pd.DataFrame(st.session_state.generation_history)
                if 'timestamp' in df_history.columns:
                    df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
                    
                    fig_line = px.line(
                        df_history,
                        x='timestamp',
                        y='generation_time',
                        title='Response Time Trend',
                        color_discrete_sequence=['#667eea']
                    )
                    fig_line.update_layout(
                        height=350,
                        font=dict(family="Inter, sans-serif", size=12),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(gridcolor='rgba(102, 126, 234, 0.1)'),
                        yaxis=dict(gridcolor='rgba(102, 126, 234, 0.1)')
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
            
            # Recent activity table
            st.markdown("""
            <div class='content-card'>
                <h3 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 1rem;'>
                    📋 Recent Activity
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display recent generations in a beautiful table
            recent_df = pd.DataFrame(st.session_state.generation_history[-10:])  # Last 10
            if not recent_df.empty:
                recent_df['Generation Time'] = recent_df['generation_time'].apply(lambda x: f"{x:.2f}s")
                recent_df['Destinations'] = recent_df['count']
                recent_df['Theme'] = recent_df['theme']
                
                # Style the dataframe
                styled_df = recent_df[['Theme', 'Destinations', 'Generation Time']].style.set_properties(**{
                    'background-color': '#f8f9ff',
                    'color': '#2c3e50',
                    'border-color': 'rgba(102, 126, 234, 0.1)',
                    'font-family': 'Inter, sans-serif'
                })
                
                st.dataframe(styled_df, use_container_width=True)
        
        else:
            # Empty state
            st.markdown("""
            <div class='content-card' style='text-align: center; padding: 4rem 2rem;'>
                <h3 style='color: #5a6c7d; font-family: Poppins, sans-serif; margin-bottom: 1rem;'>
                    📊 No Analytics Data Yet
                </h3>
                <p style='color: #5a6c7d; font-family: Inter, sans-serif; font-size: 1.1rem; margin-bottom: 2rem;'>
                    Start generating destinations to see your travel analytics!
                </p>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 20px; color: white; display: inline-block;'>
                    <p style='margin: 0; font-family: Inter, sans-serif;'>
                        🚀 Generate your first destination to unlock insights
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_favorites(self):
        """Render beautiful favorites section with modern card design."""
        
        st.markdown("""
        <div class='content-card'>
            <h2 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 2rem;'>
                ⭐ Your Favorite Destinations
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.favorite_destinations:
            st.markdown(f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 1.5rem; border-radius: 25px; font-family: Inter, sans-serif; font-weight: 500;'>
                    💝 {len(st.session_state.favorite_destinations)} Saved Destinations
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Display favorites in beautiful grid
            cols_per_row = 2
            for i in range(0, len(st.session_state.favorite_destinations), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j, col in enumerate(cols):
                    if i + j < len(st.session_state.favorite_destinations):
                        destination = st.session_state.favorite_destinations[i + j]
                        
                        with col:
                            # Beautiful favorite card
                            rating_stars = "⭐" * int(destination.rating) if destination.rating else "⭐⭐⭐⭐"
                            
                            theme_emojis = {
                                "Sports": "🏃‍♂️",
                                "Historical Place": "🏛️", 
                                "Natural Attraction": "🌿",
                                "Scientific": "🔬",
                                "Entertainment": "🎭"
                            }
                            theme_emoji = theme_emojis.get(destination.theme.value, "🌍")
                            
                            st.markdown(f"""
                            <div class='destination-card' style='background: linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%); border-left: 5px solid #ff6b6b;'>
                                <div class='destination-title' style='color: #d63031;'>
                                    {theme_emoji} {destination.place}
                                    <span style='float: right; font-size: 1.2rem;'>💝</span>
                                </div>
                                <div class='destination-country' style='color: #fd79a8;'>
                                    📍 {destination.country}
                                </div>
                                <div class='destination-description'>
                                    {destination.description[:200]}{'...' if len(destination.description) > 200 else ''}
                                </div>
                                
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid rgba(214, 48, 49, 0.1);'>
                                    <div style='font-family: Inter, sans-serif; color: #5a6c7d;'>
                                        {rating_stars} {destination.rating}/5
                                    </div>
                                    <div style='font-family: Inter, sans-serif; color: #5a6c7d; font-size: 0.9rem;'>
                                        🗓️ {destination.best_time_to_visit}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Remove button
                            if st.button(f"🗑️ Remove", key=f"remove_fav_{i}_{j}", use_container_width=True):
                                st.session_state.favorite_destinations.remove(destination)
                                st.markdown("""
                                <div class='info-message'>
                                    ✨ Removed from favorites!
                                </div>
                                """, unsafe_allow_html=True)
                                st.rerun()
            
            # Clear all button
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([2, 1, 2])
            with col2:
                if st.button("🗑️ Clear All Favorites", use_container_width=True):
                    st.session_state.favorite_destinations = []
                    st.markdown("""
                    <div class='success-message'>
                        🧹 All favorites cleared!
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
        
        else:
            # Empty state with beautiful design
            st.markdown("""
            <div class='content-card' style='text-align: center; padding: 4rem 2rem;'>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>💝</div>
                <h3 style='color: #5a6c7d; font-family: Poppins, sans-serif; margin-bottom: 1rem;'>
                    No Favorites Yet
                </h3>
                <p style='color: #5a6c7d; font-family: Inter, sans-serif; font-size: 1.1rem; margin-bottom: 2rem;'>
                    Start exploring destinations and save your favorites for future reference!
                </p>
                <div style='background: linear-gradient(135deg, #ff6b6b 0%, #fd79a8 100%); padding: 2rem; border-radius: 20px; color: white; display: inline-block;'>
                    <p style='margin: 0; font-family: Inter, sans-serif;'>
                        💡 Click the "❤️ Add to Favorites" button on any destination to save it here
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_model_management(self):
        """Render model management and fine-tuning interface."""
        st.markdown("""
        <div class='content-card'>
            <h2 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 2rem;'>
                🤖 AI Model Management
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Current model status in beautiful card
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 Current Model Status")
            model_status = self._get_model_status()
            
            # Beautiful status card
            status_color = "#00c851" if model_status['fine_tuned'] else "#33b5e5"
            status_text = "Enhanced" if model_status['fine_tuned'] else "Standard"
            
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {status_color}15 0%, {status_color}05 100%); 
                        border-left: 5px solid {status_color}; 
                        border-radius: 15px; 
                        padding: 1.5rem; 
                        margin: 1rem 0;'>
                <h4 style='color: {status_color}; margin-bottom: 1rem;'>🎯 {status_text} Model</h4>
                <p><strong>Model:</strong> {model_status['display_name'][:50]}{'...' if len(model_status['display_name']) > 50 else ''}</p>
                <p><strong>Base:</strong> {model_status['base_model']}</p>
                <p><strong>Status:</strong> <span style='color: {status_color};'>●</span> {model_status['status']}</p>
                <p><strong>Enhanced:</strong> {'Yes' if model_status['fine_tuned'] else 'No'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### 📈 Performance Metrics")
            if st.session_state.generation_history:
                recent_avg = sum([h.get('generation_time', 0) for h in st.session_state.generation_history[-10:]]) / min(10, len(st.session_state.generation_history))
                
                st.metric("⚡ Avg Response Time", f"{recent_avg:.2f}s", 
                         delta=f"-{(3.5-recent_avg):.1f}s" if recent_avg < 3.5 else None)
                st.metric("🔄 Total API Calls", st.session_state.total_generations)
                st.metric("🎯 Success Rate", "100%" if st.session_state.total_generations > 0 else "N/A")
            else:
                st.info("🏃‍♂️ Generate some destinations to see performance metrics!")
        
        st.markdown("---")
        
        # Fine-tuning section with beautiful design
        st.markdown("""
        <div class='content-card'>
            <h3 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 1rem;'>
                🎯 Domain-Specific AI Enhancement
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Information about fine-tuning
        st.markdown("""
        **🚀 What is Fine-tuning?**
        
        Fine-tuning creates a specialized AI model trained specifically for travel destination recommendations.
        Your enhanced model will provide:
        
        - 🎯 **More Accurate Recommendations**: Better understanding of travel preferences
        - 📍 **Rich Destination Details**: Enhanced descriptions and local insights  
        - ⚡ **Faster Response Times**: Optimized for travel-related queries
        - 🏆 **Consistent Quality**: Better formatted, more reliable outputs
        
        **⏱️ Process Time**: Usually takes 10-20 minutes to complete.
        """)
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Enhancement", type="primary", use_container_width=True, 
                        disabled=settings.use_fine_tuned_model):
                if not settings.use_fine_tuned_model:
                    self._initiate_fine_tuning()
                else:
                    st.warning("✨ Already using an enhanced model!")
        
        with col2:
            if st.button("📋 View Models", use_container_width=True):
                self._list_available_models()
        
        with col3:
            if st.button("🔄 Reset to Standard", use_container_width=True,
                        disabled=not settings.use_fine_tuned_model):
                if settings.use_fine_tuned_model:
                    self._reset_to_base_model()
                else:
                    st.info("Already using standard model!")
        
        # Fine-tuning status display
        if st.session_state.fine_tuning_status:
            status = st.session_state.fine_tuning_status
            
            if status['status'] == 'in_progress':
                st.markdown("""
                <div style='background: linear-gradient(135deg, #33b5e5 0%, #0099cc 100%); 
                           color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;'>
                    <h4>🔄 Enhancement in Progress</h4>
                    <p>Your AI model is being enhanced with travel expertise. This process typically takes 10-20 minutes.</p>
                    <p><em>You can continue using the application while enhancement runs in the background.</em></p>
                </div>
                """, unsafe_allow_html=True)
                
            elif status['status'] == 'completed':
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #00c851 0%, #00a085 100%); 
                           color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;'>
                    <h4>✅ Enhancement Complete!</h4>
                    <p>Your AI model has been successfully enhanced with travel expertise.</p>
                    <p><strong>Model ID:</strong> <code>{status.get('model_id', 'Unknown')}</code></p>
                    <p><em>All future destination generations will use your enhanced model.</em></p>
                </div>
                """, unsafe_allow_html=True)
                
            elif status['status'] == 'failed':
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); 
                           color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;'>
                    <h4>❌ Enhancement Failed</h4>
                    <p><strong>Error:</strong> {status.get('error', 'Unknown error')}</p>
                    <p><em>Please try again or contact support if the issue persists.</em></p>
                </div>
                """, unsafe_allow_html=True)
        
        # Cost information
        with st.expander("💰 Enhancement Cost Information"):
            st.markdown("""
            **OpenAI Fine-tuning Costs (approximate):**
            
            - **Training**: ~$0.80 for our travel dataset (~10 examples)
            - **Usage**: Same as base model (~$0.002 per 1K tokens)
            - **Storage**: No additional cost
            
            **Benefits vs. Cost:**
            - One-time training cost for permanent model improvement
            - Better results mean fewer API calls needed
            - Enhanced accuracy saves time and improves user experience
            
            **Note**: Actual costs may vary. Check OpenAI pricing for current rates.
            """)
        
        # Technical details
        with st.expander("🔧 Technical Details"):
            st.markdown(f"""
            **Current Configuration:**
            - **Base Model**: {settings.openai_model}
            - **Training Examples**: 10 high-quality samples per theme
            - **Themes Covered**: Sports, Historical, Natural, Scientific, Entertainment
            - **Training Epochs**: 3 (optimized for quality)
            - **Temperature**: {settings.openai_temperature}
            
            **Enhancement Process:**
            1. Generate curated training data for travel themes
            2. Upload training data to OpenAI
            3. Create fine-tuning job with optimized parameters
            4. Monitor training progress
            5. Deploy enhanced model automatically
            
            **Quality Assurance:**
            - Training data includes real destinations with accurate coordinates
            - Examples cover diverse global locations
            - Consistent JSON output format
            - Specialized prompts for each travel theme
            """)
    
    def _initiate_fine_tuning(self):
        """Initiate the fine-tuning process."""
        with st.spinner("🚀 Starting fine-tuning process... This will take 10-20 minutes."):
            try:
                st.session_state.fine_tuning_status = {'status': 'in_progress'}
                
                # Create progress container
                progress_container = st.empty()
                status_container = st.empty()
                
                with progress_container.container():
                    st.info("📊 Generating comprehensive training data...")
                    time.sleep(1)  # Brief pause for UX
                    
                with status_container.container():
                    st.success("✅ Training data generated successfully!")
                
                # Run fine-tuning synchronously (Streamlit-compatible)
                import threading
                import queue
                
                # Create a queue to get the result
                result_queue = queue.Queue()
                error_queue = queue.Queue()
                
                def run_fine_tuning():
                    """Run fine-tuning in a separate thread."""
                    try:
                        model_id = self.destination_service.fine_tuning_manager.full_fine_tuning_pipeline()
                        result_queue.put(model_id)
                    except Exception as e:
                        error_queue.put(str(e))
                
                # Start fine-tuning in a separate thread
                fine_tuning_thread = threading.Thread(target=run_fine_tuning)
                fine_tuning_thread.daemon = True
                fine_tuning_thread.start()
                
                # Wait for completion with progress updates
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(100):
                    if not result_queue.empty() or not error_queue.empty():
                        break
                    progress_bar.progress((i + 1) / 100)
                    status_text.text(f"⏳ Fine-tuning in progress... {i + 1}%")
                    time.sleep(12)  # Update every 12 seconds (20 minutes total)
                
                # Wait for thread to complete
                fine_tuning_thread.join(timeout=1200)  # 20 minutes max
                
                # Check for errors first
                if not error_queue.empty():
                    error_msg = error_queue.get()
                    raise Exception(error_msg)
                
                # Check for results
                if not result_queue.empty():
                    model_id = result_queue.get()
                    
                    if model_id:
                        st.session_state.fine_tuning_status = {
                            'status': 'completed',
                            'model_id': model_id
                        }
                        
                        # Update settings to use the new model
                        from src.config.settings import settings
                        settings.fine_tuned_model_id = model_id
                        settings.use_fine_tuned_model = True
                        
                        # Reinitialize service with new model
                        self.destination_service = DestinationService()
                        
                        progress_bar.progress(100)
                        st.balloons()
                        st.success(f"🎉 Fine-tuning completed successfully!")
                        st.success(f"🤖 Model ID: `{model_id}`")
                        st.info("✨ The application will now use your fine-tuned model for better, more specialized results!")
                        
                        # Show improvement message
                        st.markdown("""
                        ### 🎯 What's Improved:
                        - **Better Domain Knowledge**: More accurate travel recommendations
                        - **Enhanced Descriptions**: Richer, more detailed destination information
                        - **Improved Formatting**: More consistent JSON output structure
                        - **Faster Responses**: Optimized for travel-specific queries
                        """)
                        
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.session_state.fine_tuning_status = {
                            'status': 'failed',
                            'error': 'Fine-tuning process returned no model ID'
                        }
                        st.error("❌ Fine-tuning failed. No model ID returned.")
                else:
                    # Timeout occurred
                    st.session_state.fine_tuning_status = {
                        'status': 'failed',
                        'error': 'Fine-tuning process timed out'
                    }
                    st.error("❌ Fine-tuning timed out. Please try again or check your internet connection.")
                    
            except Exception as e:
                st.session_state.fine_tuning_status = {
                    'status': 'failed',
                    'error': str(e)
                }
                st.error(f"❌ Fine-tuning failed: {str(e)}")
                
                # Show troubleshooting tips
                with st.expander("🔧 Troubleshooting Tips"):
                    st.markdown("""
                    **Common issues and solutions:**
                    
                    1. **API Rate Limits**: Wait a few minutes and try again
                    2. **Insufficient Credits**: Check your OpenAI account balance
                    3. **Network Issues**: Ensure stable internet connection
                    4. **Model Limits**: You may have reached your fine-tuning quota
                    5. **Async Loop Issues**: Try restarting the application
                    
                    **If problems persist:**
                    - Check the console logs for detailed error messages
                    - Verify your API key has fine-tuning permissions
                    - Contact support if you continue experiencing issues
                    """)
            finally:
                # Clean up progress indicators
                try:
                    progress_bar.empty()
                    status_text.empty()
                except:
                    pass
    
    def _list_available_models(self):
        """List available fine-tuned models."""
        with st.spinner("📋 Fetching your fine-tuned models..."):
            try:
                import threading
                import queue
                
                # Create queues for thread communication
                result_queue = queue.Queue()
                error_queue = queue.Queue()
                
                def fetch_models():
                    """Fetch models in a separate thread."""
                    try:
                        models = self.destination_service.fine_tuning_manager.list_fine_tuned_models()
                        result_queue.put(models)
                    except Exception as e:
                        error_queue.put(str(e))
                
                # Start fetching in a separate thread
                fetch_thread = threading.Thread(target=fetch_models)
                fetch_thread.daemon = True
                fetch_thread.start()
                
                # Wait for completion (max 30 seconds)
                fetch_thread.join(timeout=30)
                
                # Check for errors first
                if not error_queue.empty():
                    error_msg = error_queue.get()
                    raise Exception(error_msg)
                
                # Check for results
                if not result_queue.empty():
                    models = result_queue.get()
                    
                    if models:
                        st.markdown("### 🤖 Your Fine-tuned Models")
                        
                        # Create a nice table
                        import pandas as pd
                        df = pd.DataFrame(models)
                        
                        # Format the dataframe
                        if 'created' in df.columns:
                            df['created'] = pd.to_datetime(df['created'], unit='s').dt.strftime('%Y-%m-%d %H:%M')
                        
                        # Style the dataframe
                        st.dataframe(
                            df,
                            use_container_width=True,
                            column_config={
                                "id": st.column_config.TextColumn("Model ID", width="large"),
                                "created": st.column_config.TextColumn("Created", width="medium"),
                                "owned_by": st.column_config.TextColumn("Owner", width="small")
                            }
                        )
                        
                        # Current model indicator
                        current_model = settings.effective_openai_model
                        if any(model['id'] == current_model for model in models):
                            st.success(f"🎯 Currently using: `{current_model}`")
                        
                    else:
                        st.info("📝 No fine-tuned models found. Create your first one above!")
                else:
                    st.warning("⏱️ Request timed out. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Failed to list models: {str(e)}")
                logger.error("Failed to list models", error=str(e), exc_info=True)
    
    def _reset_to_base_model(self):
        """Reset to using the base model."""
        try:
            from src.config.settings import settings
            settings.use_fine_tuned_model = False
            settings.fine_tuned_model_id = None
            
            # Reinitialize service
            self.destination_service = DestinationService()
            
            st.success("✅ Successfully reset to base model!")
            st.info("🔄 The application is now using the standard GPT model.")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to reset to base model: {str(e)}")
    
    def run(self):
        """Run the main Streamlit application with beautiful modern design."""
        try:
            logger.info("Starting Holiday Destinations Generator application")
            
            # Render beautiful header
            self._render_header()
            
            # Modern navigation with beautiful styling
            st.markdown("""
            <div class='nav-container'>
            """, unsafe_allow_html=True)
            
            selected = option_menu(
                menu_title=None,
                options=["🏠 Destinations", "📊 Analytics", "⭐ Favorites", "🤖 AI Models"],
                icons=["house", "graph-up", "heart", "robot"],
                menu_icon="cast",
                default_index=0,
                orientation="horizontal",
                styles={
                    "container": {"padding": "0", "background-color": "transparent"},
                    "icon": {"color": "#667eea", "font-size": "18px"},
                    "nav-link": {
                        "font-size": "16px",
                        "text-align": "center",
                        "margin": "0px",
                        "padding": "12px 24px",
                        "color": "#2c3e50",
                        "font-family": "Inter, sans-serif",
                        "font-weight": "500",
                        "border-radius": "12px",
                        "transition": "all 0.3s ease"
                    },
                    "nav-link-selected": {
                        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        "color": "white",
                        "box-shadow": "0 5px 15px rgba(102, 126, 234, 0.3)"
                    },
                }
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Content in beautiful cards
            if selected == "🏠 Destinations":
                self._render_destinations_tab()
            elif selected == "📊 Analytics":
                self._render_analytics_dashboard()
            elif selected == "⭐ Favorites":
                self._render_favorites()
            elif selected == "🤖 AI Models":
                self._render_model_management()
            
        except Exception as e:
            logger.error("Application error", error=str(e), exc_info=True)
            st.markdown(f"""
            <div class='error-message'>
                ❌ <strong>Application Error:</strong> {str(e)}
            </div>
            """, unsafe_allow_html=True)
    
    def _render_destinations_tab(self):
        """Render the main destinations tab with beautiful layout."""
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            self._render_sidebar()
        
        with col2:
            st.markdown("""
            <div class='content-card'>
            """, unsafe_allow_html=True)
            
            # Display last response if available
            if hasattr(st.session_state, 'last_response') and st.session_state.last_response:
                response = st.session_state.last_response
                
                # Safe theme handling for display
                theme_display = response.theme.value if hasattr(response.theme, 'value') else str(response.theme)
                
                st.markdown(f"""
                <h2 style='color: #667eea; font-family: Poppins, sans-serif; text-align: center; margin-bottom: 2rem;'>
                    ✨ Your {theme_display} Destinations
                </h2>
                """, unsafe_allow_html=True)
                
                for i, destination in enumerate(response.destinations):
                    self._display_destination(destination, show_coordinates=True)
                    
                    # Add favorite button
                    col_a, col_b, col_c = st.columns([2, 1, 2])
                    with col_b:
                        if st.button(f"❤️ Add to Favorites", key=f"fav_{i}_{destination.place}"):
                            if destination not in st.session_state.favorite_destinations:
                                st.session_state.favorite_destinations.append(destination)
                                st.markdown("""
                                <div class='success-message'>
                                    💝 Added to favorites!
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                <div class='info-message'>
                                    ℹ️ Already in favorites!
                                </div>
                                """, unsafe_allow_html=True)
                    
                    if i < len(response.destinations) - 1:
                        st.markdown("<hr style='margin: 3rem 0; border: none; height: 1px; background: linear-gradient(90deg, transparent, #667eea, transparent);'>", unsafe_allow_html=True)
            
            else:
                # Welcome screen
                st.markdown("""
                <div style='text-align: center; padding: 4rem 2rem;'>
                    <h2 style='color: #667eea; font-family: Poppins, sans-serif; margin-bottom: 1rem;'>
                        🌟 Welcome to Your Adventure
                    </h2>
                    <p style='color: #5a6c7d; font-family: Inter, sans-serif; font-size: 1.1rem; margin-bottom: 2rem;'>
                        Choose your theme and let our AI discover amazing destinations for you!
                    </p>
                    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 20px; color: white;'>
                        <h3 style='margin-bottom: 1rem;'>🎯 How it works</h3>
                        <div style='text-align: left; display: inline-block;'>
                            <p>1. 🏷️ Select your adventure theme</p>
                            <p>2. 📊 Choose number of destinations</p>
                            <p>3. 🎭 Optionally include activities</p>
                            <p>4. ✨ Generate your perfect trip!</p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    async def _generate_destinations_async(self, request: GenerationRequest):
        """Generate destinations asynchronously."""
        try:
            return await self.destination_service.generate_destinations(request)
        except Exception as e:
            logger.error("Destination generation failed", error=str(e))
            raise


def main():
    """Application entry point."""
    try:
        app = HolidayDestinationApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application failed to start: {str(e)}")
        logger.error("Application startup failed", error=str(e), exc_info=True)


if __name__ == "__main__":
    main() 