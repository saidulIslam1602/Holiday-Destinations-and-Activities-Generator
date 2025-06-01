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
            page_title="Holiday Destinations Generator",
            page_icon="🌍",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/yourusername/holiday-destinations-generator',
                'Report a bug': 'https://github.com/yourusername/holiday-destinations-generator/issues',
                'About': f"Holiday Destinations Generator v{settings.app_version} - Enterprise Edition"
            }
        )
    
    def _setup_custom_css(self):
        """Setup custom CSS for modern styling."""
        st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        
        .stSelectbox > div > div > select {
            background-color: #f0f2f6;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 16px;
        }
        
        .destination-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .activity-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
            border-left: 4px solid #007bff;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .success-message {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .error-message {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
        
        .info-box {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        
        .sidebar .sidebar-content {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        
        .model-status {
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 5px;
            padding: 0.5rem;
            margin: 0.5rem 0;
            font-size: 0.9rem;
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
        """Render application header with branding."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='color: #667eea; font-size: 3rem; margin-bottom: 0;'>
                    🌍 Holiday Destinations Generator
                </h1>
                <p style='color: #666; font-size: 1.2rem; margin-top: 0;'>
                    Enterprise Edition - Discover Your Next Adventure
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Model status indicator
            model_status = self._get_model_status()
            st.markdown(f"""
            <div class='model-status'>
                <strong>🤖 Current Model:</strong> {model_status['display_name']}<br>
                <strong>🎯 Fine-tuned:</strong> {'Yes' if model_status['fine_tuned'] else 'No'}<br>
                <strong>⚡ Status:</strong> {model_status['status']}
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
        """Render enhanced sidebar with settings and info."""
        with st.sidebar:
            st.markdown("""
            <div class='info-box'>
                <h3>🎯 Generate Destinations</h3>
                <p>Select your preferred theme and get personalized destination recommendations.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Theme selection
            theme = st.selectbox(
                "🏷️ Choose Your Theme",
                options=[theme.value for theme in ThemeType],
                help="Select the type of destinations you're interested in"
            )
            
            # Number of destinations
            count = st.slider(
                "📊 Number of Destinations",
                min_value=1,
                max_value=10,
                value=5,
                help="How many destinations would you like to generate?"
            )
            
            # Advanced options
            with st.expander("🔧 Advanced Options"):
                include_activities = st.checkbox(
                    "Include Activities",
                    value=True,
                    help="Generate specific activities for each destination"
                )
                
                show_coordinates = st.checkbox(
                    "Show Coordinates",
                    value=False,
                    help="Display latitude and longitude coordinates"
                )
                
                show_ratings = st.checkbox(
                    "Show Ratings",
                    value=True,
                    help="Display destination ratings"
                )
            
            # Generate button
            generate_clicked = st.button(
                "🚀 Generate Destinations",
                type="primary",
                use_container_width=True
            )
            
            # Statistics
            st.markdown("---")
            st.markdown("### 📈 Statistics")
            st.metric("Total Generations", st.session_state.total_generations)
            st.metric("Favorites", len(st.session_state.favorite_destinations))
            
            if st.session_state.last_generation_time:
                st.metric("Last Generation", f"{st.session_state.last_generation_time:.2f}s")
            
            # Health check
            if st.button("🔍 Health Check", use_container_width=True):
                self._perform_health_check()
            
            return theme, count, include_activities, show_coordinates, show_ratings, generate_clicked
    
    def _perform_health_check(self):
        """Perform and display health check results."""
        with st.spinner("Performing health check..."):
            try:
                health_result = asyncio.run(self.destination_service.health_check())
                
                if health_result["status"] == "healthy":
                    st.success(f"✅ System healthy - Response time: {health_result['response_time_seconds']:.2f}s")
                    
                    # Display model information
                    model_info = health_result.get('model_info', {})
                    st.info(f"""
                    **Model Information:**
                    - Current Model: {model_info.get('current_model', 'Unknown')}
                    - Base Model: {model_info.get('base_model', 'Unknown')}
                    - Fine-tuned: {'Yes' if model_info.get('fine_tuned') else 'No'}
                    """)
                else:
                    st.error(f"❌ System unhealthy: {health_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                st.error(f"❌ Health check failed: {str(e)}")
    
    async def _generate_destinations_async(self, request: GenerationRequest):
        """Generate destinations asynchronously."""
        try:
            return await self.destination_service.generate_destinations(request)
        except Exception as e:
            logger.error("Destination generation failed", error=str(e))
            raise
    
    def _display_destination(self, destination, show_coordinates=False, show_ratings=True):
        """Display a single destination with enhanced formatting."""
        
        # Main destination card
        st.markdown(f"""
        <div class='destination-card'>
            <h2>🏛️ {destination.place}</h2>
            <h4>📍 {destination.country}</h4>
            {f"<p>⭐ Rating: {destination.rating}/5" if show_ratings and destination.rating else ""}
            {f"<p>📅 Best time to visit: {destination.best_time_to_visit}</p>" if destination.best_time_to_visit else ""}
            {f"<p>📝 {destination.description}</p>" if destination.description else ""}
        </div>
        """, unsafe_allow_html=True)
        
        # Coordinates (if requested)
        if show_coordinates and destination.coordinates:
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"🌐 Latitude: {destination.coordinates['lat']}")
            with col2:
                st.info(f"🌐 Longitude: {destination.coordinates['lng']}")
        
        # Activities
        if destination.activities:
            st.markdown("### 🎯 Recommended Activities")
            
            # Create tabs for different activity types
            activity_types = list(set([act.activity_type.value for act in destination.activities if act.activity_type]))
            
            if activity_types:
                tabs = st.tabs(activity_types)
                
                for i, activity_type in enumerate(activity_types):
                    with tabs[i]:
                        type_activities = [act for act in destination.activities if act.activity_type and act.activity_type.value == activity_type]
                        
                        for activity in type_activities:
                            self._display_activity(activity)
            else:
                # Fallback: display all activities
                for activity in destination.activities:
                    self._display_activity(activity)
        
        # Favorite button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button(f"❤️ Add to Favorites", key=f"fav_{destination.id}"):
                if destination not in st.session_state.favorite_destinations:
                    st.session_state.favorite_destinations.append(destination)
                    st.success("Added to favorites!")
                else:
                    st.info("Already in favorites!")
    
    def _display_activity(self, activity):
        """Display a single activity with enhanced formatting."""
        
        difficulty_icons = {1: "🟢", 2: "🔵", 3: "🟡", 4: "🟠", 5: "🔴"}
        difficulty_icon = difficulty_icons.get(activity.difficulty_level, "⚪")
        
        st.markdown(f"""
        <div class='activity-card'>
            <h4>🎯 {activity.name}</h4>
            {f"<p><strong>Description:</strong> {activity.description}</p>" if activity.description else ""}
            <div style='display: flex; justify-content: space-between; margin-top: 1rem;'>
                {f"<span>⏱️ Duration: {activity.duration_hours}h</span>" if activity.duration_hours else ""}
                {f"<span>{difficulty_icon} Difficulty: {activity.difficulty_level}/5</span>" if activity.difficulty_level else ""}
                {f"<span>💰 Cost: {activity.cost_estimate}</span>" if activity.cost_estimate else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_analytics_dashboard(self):
        """Render analytics dashboard."""
        st.markdown("## 📊 Analytics Dashboard")
        
        if not st.session_state.generation_history:
            st.info("📈 Generate some destinations to see analytics!")
            return
        
        # Create metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class='metric-card'>
                <h3>Total Generations</h3>
                <h1 style='color: #667eea;'>{}</h1>
            </div>
            """.format(st.session_state.total_generations), unsafe_allow_html=True)
        
        with col2:
            avg_time = sum([h.get('generation_time', 0) for h in st.session_state.generation_history]) / len(st.session_state.generation_history)
            st.markdown("""
            <div class='metric-card'>
                <h3>Avg Generation Time</h3>
                <h1 style='color: #667eea;'>{:.2f}s</h1>
            </div>
            """.format(avg_time), unsafe_allow_html=True)
        
        with col3:
            themes_used = [h.get('theme') for h in st.session_state.generation_history]
            most_popular = max(set(themes_used), key=themes_used.count) if themes_used else "None"
            st.markdown("""
            <div class='metric-card'>
                <h3>Popular Theme</h3>
                <h2 style='color: #667eea;'>{}</h2>
            </div>
            """.format(most_popular), unsafe_allow_html=True)
        
        with col4:
            total_destinations = sum([h.get('destinations_count', 0) for h in st.session_state.generation_history])
            st.markdown("""
            <div class='metric-card'>
                <h3>Total Destinations</h3>
                <h1 style='color: #667eea;'>{}</h1>
            </div>
            """.format(total_destinations), unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Theme distribution
            theme_counts = {}
            for h in st.session_state.generation_history:
                theme = h.get('theme', 'Unknown')
                theme_counts[theme] = theme_counts.get(theme, 0) + 1
            
            if theme_counts:
                fig = px.pie(
                    values=list(theme_counts.values()),
                    names=list(theme_counts.keys()),
                    title="Theme Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Generation time trend
            if len(st.session_state.generation_history) > 1:
                times = [h.get('generation_time', 0) for h in st.session_state.generation_history]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    y=times,
                    mode='lines+markers',
                    name='Generation Time',
                    line=dict(color='#667eea')
                ))
                fig.update_layout(title="Generation Time Trend", yaxis_title="Time (seconds)")
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_favorites(self):
        """Render favorites page."""
        st.markdown("## ❤️ Your Favorite Destinations")
        
        if not st.session_state.favorite_destinations:
            st.info("💝 No favorites yet! Generate some destinations and add them to your favorites.")
            return
        
        # Clear favorites button
        if st.button("🗑️ Clear All Favorites", type="secondary"):
            st.session_state.favorite_destinations = []
            st.success("Favorites cleared!")
            st.experimental_rerun()
        
        # Display favorites
        for i, destination in enumerate(st.session_state.favorite_destinations):
            with st.expander(f"🏛️ {destination.place}, {destination.country}"):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    self._display_destination(destination, show_coordinates=True, show_ratings=True)
                
                with col2:
                    if st.button("❌ Remove", key=f"remove_{i}"):
                        st.session_state.favorite_destinations.pop(i)
                        st.success("Removed from favorites!")
                        st.experimental_rerun()
    
    def _render_model_management(self):
        """Render model management and fine-tuning interface."""
        st.markdown("## 🤖 AI Model Management")
        
        # Current model status
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Current Model Status")
            model_status = self._get_model_status()
            
            st.info(f"""
            **Current Model:** {model_status['display_name']}
            
            **Base Model:** {model_status['base_model']}
            
            **Fine-tuned:** {'Yes' if model_status['fine_tuned'] else 'No'}
            
            **Status:** {model_status['status']}
            """)
        
        with col2:
            st.markdown("### Model Performance")
            if st.session_state.generation_history:
                recent_avg = sum([h.get('generation_time', 0) for h in st.session_state.generation_history[-10:]]) / min(10, len(st.session_state.generation_history))
                st.metric("Avg Response Time (Recent)", f"{recent_avg:.2f}s")
                st.metric("Total API Calls", st.session_state.total_generations)
            else:
                st.info("No performance data available yet.")
        
        st.markdown("---")
        
        # Fine-tuning section
        st.markdown("### 🎯 Domain-Specific Fine-Tuning")
        
        st.markdown("""
        Fine-tuning creates a specialized model trained specifically for travel destination recommendations.
        This improves response quality, accuracy, and domain expertise.
        
        **Benefits:**
        - More accurate and detailed destination recommendations
        - Better understanding of travel terminology and contexts
        - Improved activity suggestions based on location expertise
        - Faster response times for travel-related queries
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Start Fine-Tuning", type="primary", use_container_width=True):
                if not settings.use_fine_tuned_model:
                    self._initiate_fine_tuning()
                else:
                    st.warning("Already using a fine-tuned model!")
        
        with col2:
            if st.button("📋 List Models", use_container_width=True):
                self._list_available_models()
        
        with col3:
            if st.button("🔄 Reset to Base Model", use_container_width=True):
                self._reset_to_base_model()
        
        # Fine-tuning status
        if st.session_state.fine_tuning_status:
            st.markdown("### Fine-Tuning Status")
            status = st.session_state.fine_tuning_status
            
            if status['status'] == 'in_progress':
                st.warning(f"🔄 Fine-tuning in progress... Job ID: {status.get('job_id', 'Unknown')}")
            elif status['status'] == 'completed':
                st.success(f"✅ Fine-tuning completed! Model ID: {status.get('model_id', 'Unknown')}")
            elif status['status'] == 'failed':
                st.error(f"❌ Fine-tuning failed: {status.get('error', 'Unknown error')}")
    
    def _initiate_fine_tuning(self):
        """Initiate the fine-tuning process."""
        with st.spinner("🚀 Starting fine-tuning process... This may take several minutes."):
            try:
                st.session_state.fine_tuning_status = {'status': 'in_progress'}
                
                # Run fine-tuning in background
                model_id = asyncio.run(self.destination_service.initiate_fine_tuning())
                
                if model_id:
                    st.session_state.fine_tuning_status = {
                        'status': 'completed',
                        'model_id': model_id
                    }
                    st.success(f"🎉 Fine-tuning completed successfully! Model ID: {model_id}")
                    st.info("The application will now use the fine-tuned model for better results!")
                    st.experimental_rerun()
                else:
                    st.session_state.fine_tuning_status = {
                        'status': 'failed',
                        'error': 'Fine-tuning process failed'
                    }
                    st.error("❌ Fine-tuning failed. Please check logs for details.")
                    
            except Exception as e:
                st.session_state.fine_tuning_status = {
                    'status': 'failed',
                    'error': str(e)
                }
                st.error(f"❌ Fine-tuning failed: {str(e)}")
    
    def _list_available_models(self):
        """List available fine-tuned models."""
        try:
            models = asyncio.run(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    self.destination_service.fine_tuning_manager.list_fine_tuned_models
                )
            )
            
            if models:
                st.markdown("### Available Fine-tuned Models")
                df = pd.DataFrame(models)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No fine-tuned models available.")
                
        except Exception as e:
            st.error(f"❌ Failed to list models: {str(e)}")
    
    def _reset_to_base_model(self):
        """Reset to using the base model."""
        try:
            settings.use_fine_tuned_model = False
            settings.fine_tuned_model_id = None
            
            # Reinitialize service
            self.destination_service = DestinationService()
            
            st.success("✅ Reset to base model successfully!")
            st.experimental_rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to reset to base model: {str(e)}")
    
    def run(self):
        """Main application entry point."""
        logger.info("Starting Holiday Destinations Generator application")
        
        # Header
        self._render_header()
        
        # Navigation
        selected = option_menu(
            menu_title=None,
            options=["🏠 Home", "📊 Analytics", "❤️ Favorites", "🤖 AI Models"],
            icons=["house", "graph-up", "heart", "cpu"],
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#667eea", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#667eea"},
            },
        )
        
        if selected == "🏠 Home":
            # Sidebar
            theme, count, include_activities, show_coordinates, show_ratings, generate_clicked = self._render_sidebar()
            
            # Main content
            if generate_clicked:
                try:
                    # Create request
                    request = GenerationRequest(
                        theme=ThemeType(theme),
                        count=count,
                        include_activities=include_activities
                    )
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔄 Generating destinations...")
                    progress_bar.progress(25)
                    
                    # Generate destinations
                    start_time = time.time()
                    
                    with st.spinner("🤖 AI is working on your destinations..."):
                        response = asyncio.run(self._generate_destinations_async(request))
                    
                    generation_time = time.time() - start_time
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Generation completed!")
                    
                    # Update session state
                    st.session_state.total_generations += 1
                    st.session_state.last_generation_time = generation_time
                    st.session_state.generation_history.append({
                        'theme': theme,
                        'count': count,
                        'generation_time': generation_time,
                        'destinations_count': len(response.destinations),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display success message
                    model_used = "Fine-tuned" if settings.use_fine_tuned_model else "Base"
                    st.markdown(f"""
                    <div class='success-message'>
                        <h4>🎉 Successfully generated {len(response.destinations)} destinations!</h4>
                        <p>⏱️ Generation time: {generation_time:.2f} seconds</p>
                        <p>🎯 Theme: {theme}</p>
                        <p>🤖 Model: {model_used} ({settings.effective_openai_model})</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display destinations
                    st.markdown("---")
                    for i, destination in enumerate(response.destinations):
                        st.markdown(f"### Destination {i + 1}")
                        self._display_destination(destination, show_coordinates, show_ratings)
                        st.markdown("---")
                    
                    logger.info(
                        "Destinations generated successfully",
                        theme=theme,
                        count=len(response.destinations),
                        generation_time=generation_time
                    )
                    
                except DestinationGenerationError as e:
                    st.markdown(f"""
                    <div class='error-message'>
                        <h4>❌ Generation Failed</h4>
                        <p>{str(e)}</p>
                        <p>Please try again with different parameters.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    logger.error("Destination generation failed", error=str(e))
                
                except Exception as e:
                    st.markdown(f"""
                    <div class='error-message'>
                        <h4>❌ Unexpected Error</h4>
                        <p>An unexpected error occurred: {str(e)}</p>
                        <p>Please contact support if this persists.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    logger.error("Unexpected error in destination generation", error=str(e), exc_info=True)
            
            else:
                # Welcome message
                st.markdown("""
                <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin: 2rem 0;'>
                    <h2>🌟 Welcome to the Enterprise Holiday Destinations Generator!</h2>
                    <p style='font-size: 1.1rem; margin-top: 1rem;'>
                        Select your preferred theme from the sidebar and click "Generate Destinations" to discover amazing places tailored to your interests.
                    </p>
                    <p style='margin-top: 1rem;'>
                        ✨ Powered by AI • 🚀 Enterprise-grade • 🔒 Secure • 📊 Analytics-enabled • 🎯 Fine-tuned Models
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Feature highlights
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("""
                    <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;'>
                        <h3>🤖 AI-Powered</h3>
                        <p>Advanced language models with domain-specific fine-tuning generate personalized recommendations.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;'>
                        <h3>🎯 Themed Discovery</h3>
                        <p>Choose from sports, historical, natural, scientific, or entertainment-focused destinations.</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown("""
                    <div style='background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;'>
                        <h3>📊 Smart Analytics</h3>
                        <p>Track your generation history and discover insights about your travel preferences.</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        elif selected == "📊 Analytics":
            self._render_analytics_dashboard()
        
        elif selected == "❤️ Favorites":
            self._render_favorites()
        
        elif selected == "🤖 AI Models":
            self._render_model_management()


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