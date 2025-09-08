"""Streamlit frontend application for HR Assistant."""

import streamlit as st
import os
import zipfile
import io
from typing import List, Dict, Any
from datetime import datetime
import uuid

# Set page config
st.set_page_config(
    page_title="HR Assistant - Hiring Planner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import our modules
try:
    from .workflow import hr_workflow
    from .session_manager import session_manager
    from .state import WorkflowStage
    from .company_profile import (
        is_company_profile_complete,
        load_company_profile,
        save_company_profile,
        CompanyProfile
    )
except ImportError:
    # For running directly
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from src.workflow import hr_workflow
    from src.session_manager import session_manager
    from src.state import WorkflowStage
    from src.company_profile import (
        is_company_profile_complete,
        load_company_profile,
        save_company_profile,
        CompanyProfile
    )


class HRAssistantApp:
    """Main Streamlit application for HR Assistant."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "session_id" not in st.session_state:
            st.session_state.session_id = str(uuid.uuid4())
        
        if "conversation_started" not in st.session_state:
            st.session_state.conversation_started = False
        
        if "current_state" not in st.session_state:
            st.session_state.current_state = None
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Check if setup wizard should be shown
        if "setup_complete" not in st.session_state:
            st.session_state.setup_complete = is_company_profile_complete()
    
    def render_header(self):
        """Render the application header."""
        st.title("🤖 HR Assistant - AI Hiring Planner")
        st.markdown("""
        Welcome to your intelligent hiring assistant! I help startups create comprehensive hiring plans.
        Just tell me what roles you need to fill, and I'll guide you through creating:
        
        📋 **Job Descriptions** • ✅ **Hiring Checklists** • ⏰ **Timelines** • 💰 **Salary Recommendations** • ❓ **Interview Questions**
        """)
        st.divider()
    
    def render_setup_wizard(self):
        """Render the company profile setup wizard."""
        st.title("🏢 Company Setup")
        st.markdown("""
        **Welcome!** Let's set up your company profile to personalize all generated hiring materials.
        
        This takes just 30 seconds and will make your job descriptions, checklists, and other materials 
        sound authentically from your company.
        """)
        
        # Load current profile (might be partially filled)
        current_profile = load_company_profile()
        
        with st.form("setup_form", clear_on_submit=False):
            st.subheader("📋 Required Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                company_name = st.text_input(
                    "Company Name *",
                    value=current_profile.name or "",
                    placeholder="e.g., Acme AI",
                    help="Your company name as it should appear in job descriptions"
                )
                
                company_size = st.selectbox(
                    "Company Size *",
                    options=["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"],
                    index=0 if not current_profile.size else ["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"].index(current_profile.size) if current_profile.size in ["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"] else 0,
                    help="Current number of employees"
                )
            
            with col2:
                funding_stage = st.selectbox(
                    "Funding Stage *",
                    options=["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"],
                    index=0 if not current_profile.stage else ["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"].index(current_profile.stage) if current_profile.stage in ["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"] else 0,
                    help="Current funding stage"
                )
                
                industry = st.text_input(
                    "Industry *",
                    value=current_profile.industry or "",
                    placeholder="e.g., AI/ML, SaaS, Fintech",
                    help="Primary industry or sector"
                )
            
            st.divider()
            st.subheader("🎨 Optional (Enhances Personalization)")
            
            col3, col4 = st.columns(2)
            
            with col3:
                location = st.text_input(
                    "Location",
                    value=current_profile.location or "",
                    placeholder="e.g., San Francisco, CA",
                    help="Primary office location"
                )
                
                remote_policy = st.selectbox(
                    "Remote Policy",
                    options=["", "Remote-first", "Hybrid", "In-office"],
                    index=0 if not current_profile.remote_policy else ["", "Remote-first", "Hybrid", "In-office"].index(current_profile.remote_policy) if current_profile.remote_policy in ["", "Remote-first", "Hybrid", "In-office"] else 0,
                    help="Work arrangement policy"
                )
            
            with col4:
                company_description = st.text_area(
                    "Company Description",
                    value=current_profile.description or "",
                    placeholder="What does your company do? (1-2 sentences)",
                    help="Brief description of your company and what you do",
                    height=100
                )
            
            company_values = st.text_area(
                "Company Values",
                value=current_profile.values or "",
                placeholder="e.g., Innovation, Integrity, Impact",
                help="Core values that guide your company (will be used in interview questions)",
                height=80
            )
            
            company_mission = st.text_area(
                "Mission/Vision",
                value=current_profile.mission or "",
                placeholder="Your company's mission statement or vision",
                help="Company mission or vision (will be included in job descriptions)",
                height=80
            )
            
            st.divider()
            
            # Form submission
            col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
            
            with col_submit2:
                submitted = st.form_submit_button(
                    "✅ Complete Setup",
                    type="primary",
                    use_container_width=True
                )
            
            if submitted:
                # Validate required fields
                if not all([company_name.strip(), company_size, funding_stage, industry.strip()]):
                    st.error("⚠️ Please fill in all required fields (marked with *)")
                else:
                    # Create and save profile
                    profile = CompanyProfile(
                        name=company_name.strip(),
                        size=company_size,
                        stage=funding_stage,
                        industry=industry.strip(),
                        location=location.strip() if location.strip() else None,
                        remote_policy=remote_policy if remote_policy else None,
                        description=company_description.strip() if company_description.strip() else None,
                        values=company_values.strip() if company_values.strip() else None,
                        mission=company_mission.strip() if company_mission.strip() else None
                    )
                    
                    if save_company_profile(profile):
                        st.session_state.setup_complete = True
                        st.success("🎉 Company profile saved! You're ready to start hiring.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Failed to save company profile. Please try again.")
    
    def render_company_settings(self):
        """Render company settings in sidebar for editing profile."""
        profile = load_company_profile()
        
        # Show current company info in a compact format
        if is_company_profile_complete():
            st.success(f"✅ **{profile.name}**")
            st.caption(f"{profile.size} • {profile.stage} • {profile.industry}")
        else:
            st.warning("⚠️ Profile incomplete")
        
        # Settings expander
        with st.expander("⚙️ Edit Settings", expanded=False):
            st.markdown("**Update your company profile:**")
            
            # Form for editing
            with st.form("settings_form", clear_on_submit=False):
                st.subheader("📋 Required")
                
                company_name = st.text_input(
                    "Company Name",
                    value=profile.name or "",
                    placeholder="e.g., Acme AI"
                )
                
                company_size = st.selectbox(
                    "Company Size",
                    options=["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"],
                    index=0 if not profile.size else ["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"].index(profile.size) if profile.size in ["", "1-10 employees", "10-50 employees", "50-200 employees", "200+ employees"] else 0
                )
                
                funding_stage = st.selectbox(
                    "Funding Stage",
                    options=["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"],
                    index=0 if not profile.stage else ["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"].index(profile.stage) if profile.stage in ["", "Pre-seed", "Seed", "Series A", "Series B", "Series C+", "Profitable/Bootstrapped"] else 0
                )
                
                industry = st.text_input(
                    "Industry",
                    value=profile.industry or "",
                    placeholder="e.g., AI/ML, SaaS"
                )
                
                st.divider()
                st.subheader("🎨 Optional")
                
                location = st.text_input(
                    "Location",
                    value=profile.location or "",
                    placeholder="e.g., San Francisco, CA"
                )
                
                remote_policy = st.selectbox(
                    "Remote Policy",
                    options=["", "Remote-first", "Hybrid", "In-office"],
                    index=0 if not profile.remote_policy else ["", "Remote-first", "Hybrid", "In-office"].index(profile.remote_policy) if profile.remote_policy in ["", "Remote-first", "Hybrid", "In-office"] else 0
                )
                
                company_description = st.text_area(
                    "Description",
                    value=profile.description or "",
                    placeholder="What does your company do?",
                    height=80
                )
                
                company_values = st.text_area(
                    "Values",
                    value=profile.values or "",
                    placeholder="e.g., Innovation, Integrity",
                    height=60
                )
                
                company_mission = st.text_area(
                    "Mission/Vision",
                    value=profile.mission or "",
                    placeholder="Your company's mission",
                    height=60
                )
                
                # Form button
                save_clicked = st.form_submit_button("✅ Save", type="primary")
                
                if save_clicked:
                    # Validate required fields
                    if not all([company_name.strip(), company_size, funding_stage, industry.strip()]):
                        st.error("⚠️ Please fill in all required fields")
                    else:
                        # Create updated profile
                        updated_profile = CompanyProfile(
                            name=company_name.strip(),
                            size=company_size,
                            stage=funding_stage,
                            industry=industry.strip(),
                            location=location.strip() if location.strip() else None,
                            remote_policy=remote_policy if remote_policy else None,
                            description=company_description.strip() if company_description.strip() else None,
                            values=company_values.strip() if company_values.strip() else None,
                            mission=company_mission.strip() if company_mission.strip() else None
                        )
                        
                        if save_company_profile(updated_profile):
                            st.success("✅ Settings saved!")
                            # Check if setup is still complete after save
                            st.session_state.setup_complete = is_company_profile_complete()
                            st.rerun()
                        else:
                            st.error("❌ Failed to save settings")
    
    def render_sidebar(self):
        """Render the sidebar with session management."""
        with st.sidebar:
            st.header("🔧 Session Management")
            
            # Current session info
            st.info(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
            
            # New session button
            if st.button("🆕 Start New Session", type="secondary"):
                self.start_new_session()
            
            st.divider()
            
            # Session history
            st.header("📚 Session History")
            self.render_session_history()
            
            st.divider()
            
            # Company Settings
            st.header("🏢 Company Settings")
            self.render_company_settings()
            
            st.divider()
            
            # Example prompts section
            st.header("🚀 Quick Examples")
            # Only show if no conversation is started
            if not st.session_state.conversation_started:
                st.markdown("**Try these examples:**")
                
                if st.button("💻 Technical Roles", use_container_width=True):
                    example = "I need to hire a senior software engineer and a DevOps engineer"
                    self.start_conversation(example)
                
                if st.button("🚀 Founding Team", use_container_width=True):
                    example = "I need to hire a founding engineer and a GenAI intern"
                    self.start_conversation(example)
                    
                if st.button("📈 Growth Roles", use_container_width=True):
                    example = "I need to hire a product manager and a marketing specialist"
                    self.start_conversation(example)
            else:
                st.caption("💬 Examples available when starting new session")
            
            st.divider()
            
            # App info
            st.header("ℹ️ About")
            st.markdown("""
            **HR Assistant** uses:
            - 🧠 **GPT-4o-mini** for intelligent content generation
            - 🔄 **LangGraph** for workflow orchestration  
            - 💾 **Session Persistence** to save your progress
            - 📁 **File Export** for all generated materials
            """)
    
    def render_session_history(self):
        """Render session history in sidebar."""
        sessions = session_manager.list_sessions()
        
        if not sessions:
            st.write("No previous sessions")
            return
        
        for session in sessions[:5]:  # Show last 5 sessions
            with st.expander(f"Session {session['session_id'][:8]}..."):
                st.write(f"**Request:** {session['original_request'][:50]}...")
                st.write(f"**Roles:** {', '.join(session['job_roles'][:3])}")
                st.write(f"**Status:** {'✅ Complete' if session['completed'] else '⏳ In Progress'}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{session['session_id']}", type="secondary"):
                        self.load_session(session['session_id'])
                with col2:
                    if st.button("Delete", key=f"del_{session['session_id']}", type="secondary"):
                        session_manager.delete_session(session['session_id'])
                        st.rerun()
    
    def start_new_session(self):
        """Start a new conversation session."""
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.conversation_started = False
        st.session_state.current_state = None
        st.session_state.messages = []  # Clear messages to show introduction
        st.rerun()
    
    def load_session(self, session_id: str):
        """Load an existing session."""
        state = session_manager.load_session(session_id)
        if state:
            st.session_state.session_id = session_id
            st.session_state.current_state = state
            st.session_state.conversation_started = True
            st.session_state.messages = state.get("messages", [])
            st.success(f"Loaded session {session_id[:8]}...")
            st.rerun()
        else:
            st.error("Failed to load session")
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        
        # Show introduction message if no conversation started and no messages
        if not st.session_state.conversation_started and not st.session_state.messages:
            self.render_introduction_message()
            st.divider()  # Add visual separation
        
        # Display conversation history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Initial prompt or continue conversation
        if not st.session_state.conversation_started:
            self.render_initial_input()
        else:
            self.render_conversation_continuation()
    
    def render_introduction_message(self):
        """Render contextual introduction message based on user's history."""
        try:
            # Get company info for personalization
            profile = load_company_profile()
            company_name = profile.name if profile and profile.name else "there"
            
            # Get session history
            sessions = session_manager.list_sessions()
            
            if not sessions:
                # New user - welcome message
                intro_message = f"👋 Hello and welcome to HR Assistant, {company_name}!\n\nI'm here to help you create comprehensive hiring plans. I can generate job descriptions, hiring checklists, timelines, salary recommendations, and interview questions for any roles you need to fill.\n\nLet's get started!"
            else:
                # Existing user - check their last session
                last_session = sessions[0]  # Sessions are ordered by most recent first
                
                if last_session['completed']:
                    # Last session was completed
                    roles_text = ", ".join(last_session['job_roles'][:2])
                    if len(last_session['job_roles']) > 2:
                        roles_text += f" and {len(last_session['job_roles']) - 2} more"
                    
                    intro_message = f"👋 Welcome back, {company_name}!\n\nLast time we completed a hiring plan for: **{roles_text}**\n\nReady to work on your next hiring project?"
                else:
                    # Last session was in progress
                    roles_text = ", ".join(last_session['job_roles'][:2])
                    if len(last_session['job_roles']) > 2:
                        roles_text += f" and {len(last_session['job_roles']) - 2} more"
                    
                    intro_message = f"👋 Welcome back, {company_name}!\n\nYou were last working on a hiring plan for: **{roles_text}**\n\nWould you like to continue where you left off, or start something new?"
            
            # Display the introduction message
            with st.chat_message("assistant"):
                st.write(intro_message)
            
            # Add continue session button for in-progress sessions (below the message)
            if sessions and not sessions[0]['completed']:
                last_session = sessions[0]
                roles_text = ", ".join(last_session['job_roles'][:2])
                if len(last_session['job_roles']) > 2:
                    roles_text += f" and {len(last_session['job_roles']) - 2} more"
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("📋 Continue Previous Session", type="primary", use_container_width=True):
                        # Add a transition message before loading
                        with st.chat_message("assistant"):
                            st.write(f"Great! Loading your previous session for {roles_text}...")
                        self.load_session(last_session['session_id'])
                        return
                
        except Exception as e:
            # Fallback to simple welcome message
            with st.chat_message("assistant"):
                st.write("👋 Welcome to HR Assistant! I'm here to help you create comprehensive hiring plans. Let's get started!")
            print(f"Error in render_introduction_message: {e}")
    
    def render_initial_input(self):
        """Render initial hiring request input."""
        st.subheader("🚀 What hiring help do you need?")
        
        # Custom input
        st.markdown("**Describe your specific needs:**")
        st.caption("💡 Example: I need to hire a senior frontend developer and a junior designer for my early-stage SaaS startup")
        user_input = st.chat_input(
            "Describe your hiring needs...",
            key="initial_input"
        )
        
        if user_input and user_input.strip():
            self.start_conversation(user_input.strip())
    
    def start_conversation(self, user_request: str):
        """Start a new conversation with the user's request."""
        try:
            with st.spinner("Analyzing your hiring needs..."):
                # First, run just the initial analysis to see if we have complete information
                from src.nodes import initial_analysis_node
                from src.state import create_initial_state
                
                initial_state = create_initial_state(user_request, st.session_state.session_id)
                analysis_result = initial_analysis_node(initial_state)
                
                # Update the state with analysis results
                updated_state = dict(initial_state)
                for key, value in analysis_result.items():
                    updated_state[key] = value
                
                # Check if we have complete information for all roles
                if updated_state.get("ready_for_generation", False):
                    # We have complete information! Show confirmation before generating
                    from src.nodes import content_generation_coordinator_node
                    
                    # Run coordinator to get confirmation message
                    coordinator_result = content_generation_coordinator_node(updated_state)
                    for key, value in coordinator_result.items():
                        updated_state[key] = value
                    
                    # Update session state to show the confirmation message
                    st.session_state.current_state = updated_state
                    st.session_state.conversation_started = True
                    st.session_state.messages = updated_state.get("messages", [])
                    session_manager.save_session(st.session_state.session_id, updated_state)
                    
                    st.rerun()
                else:
                    # Information is incomplete, run the normal workflow
                    result = hr_workflow.start_conversation(user_request, st.session_state.session_id)
                    
                    # Update session state
                    st.session_state.current_state = result
                    st.session_state.conversation_started = True
                    st.session_state.messages = result.get("messages", [])
                    
                    # Save session
                    session_manager.save_session(st.session_state.session_id, result)
                    
                    st.rerun()
                
        except Exception as e:
            error_str = str(e).lower()
            if "invalid api key" in error_str or "incorrect api key" in error_str or "authentication" in error_str:
                st.error("🔑 Invalid OpenAI API Key!")
                st.markdown("""
                Your OpenAI API key appears to be invalid or has expired. Please:
                
                1. Check your `.env` file
                2. Verify your API key is correct
                3. Ensure you have sufficient credits
                4. Restart the application
                """)
            elif "quota" in error_str or "rate limit" in error_str:
                st.error("🚫 OpenAI API Quota Exceeded!")
                st.markdown("""
                You've exceeded your OpenAI API quota or rate limit. Please:
                
                1. Check your usage at [OpenAI Platform](https://platform.openai.com/usage)
                2. Add credits to your account if needed
                3. Wait a moment and try again
                """)
            else:
                st.error(f"Error starting conversation: {e}")
                st.write("Please check your OpenAI API key and internet connection.")
    
    def render_conversation_continuation(self):
        """Render conversation continuation interface."""
        if not st.session_state.current_state:
            st.warning("No active conversation state. Please start a new session.")
            return
        
        state = st.session_state.current_state
        stage = state.get("stage")
        
        if stage == WorkflowStage.COMPLETED:
            self.render_completion_interface()
        elif state.get("pending_user_response", False):
            self.render_question_response_interface()
        else:
            self.render_status_interface()
    
    def render_question_response_interface(self):
        """Render interface for responding to questions."""
        st.subheader("💬 Please provide more information")
        
        # User input for response
        user_response = st.chat_input(
            "Please answer the questions above with as much detail as possible...",
            key="response_input"
        )
        
        if user_response and user_response.strip():
            self.continue_conversation(user_response.strip())
    
    def continue_conversation(self, user_response: str):
        """Continue the conversation with user response."""
        try:
            # Step 1: Process response and get intermediate state
            with st.spinner("Processing your response..."):
                if st.session_state.current_state:
                    # Import nodes for manual processing
                    from src.nodes import response_processing_node, content_generation_coordinator_node
                    
                    # Use current session state which has the most recent updates
                    updated_state = dict(st.session_state.current_state)
                    updated_state["user_response"] = user_response
                    
                    
                    # Process the response
                    response_result = response_processing_node(updated_state, user_response)
                    for key, value in response_result.items():
                        updated_state[key] = value
                    
                    from src.nodes import role_completion_check_node, role_focus_node, question_generation_node
                    
                    role_check_result = role_completion_check_node(updated_state)
                    for key, value in role_check_result.items():
                        updated_state[key] = value
                    
                    # Update session state after role completion check
                    st.session_state.current_state = updated_state
                    st.session_state.messages = updated_state.get("messages", [])
                    session_manager.save_session(st.session_state.session_id, updated_state)
                    
                    # Check what to do next based on role completion check result
                    if updated_state.get("ready_for_generation", False):
                        # All roles complete, run coordinator to get confirmation message
                        coordinator_result = content_generation_coordinator_node(updated_state)
                        for key, value in coordinator_result.items():
                            updated_state[key] = value
                        
                        # Update again with coordinator messages
                        st.session_state.current_state = updated_state
                        st.session_state.messages = updated_state.get("messages", [])
                        session_manager.save_session(st.session_state.session_id, updated_state)
                    elif updated_state.get("stage") == WorkflowStage.ASKING_QUESTIONS:
                        # More roles to process or need more info for current role
                        
                        # Check if we moved to a new role - only show introduction if we did
                        old_role_index = st.session_state.current_state.get("current_role_index", 0)
                        new_role_index = updated_state.get("current_role_index", 0)
                        moved_to_new_role = new_role_index > old_role_index
                        
                        # Only call role_focus_node if we actually moved to a new role
                        if moved_to_new_role:
                            role_focus_result = role_focus_node(updated_state)
                            for key, value in role_focus_result.items():
                                updated_state[key] = value
                        
                        # If still asking questions after role focus, generate questions
                        if updated_state.get("stage") == WorkflowStage.ASKING_QUESTIONS:
                            question_result = question_generation_node(updated_state)
                            for key, value in question_result.items():
                                updated_state[key] = value
                        
                        # Update session state with new questions
                        st.session_state.current_state = updated_state
                        st.session_state.messages = updated_state.get("messages", [])
                        session_manager.save_session(st.session_state.session_id, updated_state)
                    
                    st.rerun()
                else:
                    # Fallback: No session state available
                    st.error("No current session state available. Please restart the conversation.")
                    return
                
        except Exception as e:
            error_str = str(e).lower()
            if "invalid api key" in error_str or "incorrect api key" in error_str or "authentication" in error_str:
                st.error("🔑 Invalid OpenAI API Key!")
                st.markdown("""
                Your OpenAI API key appears to be invalid or has expired. Please:
                
                1. Check your `.env` file
                2. Verify your API key is correct
                3. Ensure you have sufficient credits
                4. Restart the application
                """)
            elif "quota" in error_str or "rate limit" in error_str:
                st.error("🚫 OpenAI API Quota Exceeded!")
                st.markdown("""
                You've exceeded your OpenAI API quota or rate limit. Please:
                
                1. Check your usage at [OpenAI Platform](https://platform.openai.com/usage)
                2. Add credits to your account if needed
                3. Wait a moment and try again
                """)
            else:
                st.error(f"Error processing response: {e}")
    
    def render_status_interface(self):
        """Render current status and information."""
        state = st.session_state.current_state
        
        # Show extracted information
        self.render_extracted_info()
        
        # Show current stage
        stage = state.get("stage")
        if stage == WorkflowStage.GENERATING_CONTENT:
            with st.spinner("🎨 Generating your hiring materials..."):
                st.write("Creating comprehensive hiring materials for all your roles. This may take a moment...")
                # Trigger content generation
                self.trigger_content_generation()
        elif state.get("ready_for_generation", False) and not state.get("generated_files"):
            # User is ready for generation but content generation hasn't started yet
            # This allows the intermediate messages to be shown first
            st.info("🎨 Ready to generate comprehensive hiring materials...")
            # Auto-trigger content generation after a brief moment
            self.trigger_content_generation()
    
    def trigger_content_generation(self):
        """Trigger content generation and completion."""
        try:
            state = st.session_state.current_state
            
            # Generate all content
            content_result = hr_workflow._content_generation_wrapper(state)
            for key, value in content_result.items():
                state[key] = value
            
            # Mark as completed
            completion_result = hr_workflow._completion_wrapper(state)
            for key, value in completion_result.items():
                state[key] = value
            
            # Update session state
            st.session_state.current_state = state
            st.session_state.messages = state.get("messages", [])
            session_manager.save_session(st.session_state.session_id, state)
            
            # Celebrate the completion with balloons! 🎉
            st.balloons()
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating content: {e}")
    
    def create_role_zip(self, role_name: str, role_files: Dict[str, str]) -> bytes:
        """Create a ZIP file containing all documents for a specific role."""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_type, file_path in role_files.items():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Create a clean filename
                    filename = os.path.basename(file_path)
                    zip_file.writestr(filename, content)
                except Exception as e:
                    print(f"Error adding {file_path} to ZIP: {e}")
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def render_extracted_info(self):
        """Render extracted information from conversation."""
        state = st.session_state.current_state
        
        # Job roles
        if state.get("job_roles"):
            st.subheader("🎯 Job Roles Identified")
            for i, role in enumerate(state["job_roles"]):
                with st.expander(f"{role.get('title', 'Unknown Role')}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Seniority:** {role.get('seniority_level', 'Not specified')}")
                        st.write(f"**Department:** {role.get('department', 'Not specified')}")
                    with col2:
                        skills = role.get('specific_skills', [])
                        if skills:
                            # Handle both list and string formats defensively
                            if isinstance(skills, list):
                                skills_display = ', '.join(skills)
                            elif isinstance(skills, str):
                                skills_display = skills
                            else:
                                skills_display = str(skills)
                            st.write(f"**Skills:** {skills_display}")
                        if role.get('budget_range'):
                            st.write(f"**Budget:** {role['budget_range']}")
                        if role.get('timeline'):
                            st.write(f"**Timeline:** {role['timeline']}")
        
        # Company information - show rich profile data for transparency
        try:
            from .company_profile import get_company_info_dict
        except ImportError:
            from src.company_profile import get_company_info_dict
        company_info = get_company_info_dict()
        
        if any(company_info.values()):
            st.subheader("🏢 Company Information")
            col1, col2 = st.columns(2)
            
            with col1:
                if company_info.get("name"):
                    st.write(f"**Company:** {company_info['name']}")
                if company_info.get("size"):
                    st.write(f"**Size:** {company_info['size']}")
                if company_info.get("stage"):
                    st.write(f"**Stage:** {company_info['stage']}")
                if company_info.get("industry"):
                    st.write(f"**Industry:** {company_info['industry']}")
            
            with col2:
                if company_info.get("location"):
                    st.write(f"**Location:** {company_info['location']}")
                if company_info.get("remote_policy"):
                    st.write(f"**Remote Policy:** {company_info['remote_policy']}")
            
            # Show additional rich profile fields if available
            if company_info.get("description"):
                st.write(f"**Description:** {company_info['description']}")
            if company_info.get("values"):
                st.write(f"**Values:** {company_info['values']}")
            if company_info.get("mission"):
                st.write(f"**Mission:** {company_info['mission']}")
    
    def render_completion_interface(self):
        """Render completion interface with generated files."""
        st.success("🎉 Your hiring plan is complete!")
        
        state = st.session_state.current_state
        generated_files = state.get("generated_files", {})
        
        if generated_files:
            st.subheader("📁 Generated Materials")
            
            # Organize files by role
            files_by_role = {}
            for file_key, file_path in generated_files.items():
                # Extract role from filename
                # Format: file_type_role_name or multi_word_file_type_role_name
                parts = file_key.split('_')
                if len(parts) >= 3:
                    # Find the last part that's clearly the role name (usually 2+ words)
                    # Common patterns: job_description_role, hiring_checklist_role, interview_questions_role
                    if file_key.startswith('job_description_'):
                        file_type = 'job_description'
                        role_name = file_key[len('job_description_'):].replace('_', ' ').title()
                    elif file_key.startswith('hiring_checklist_'):
                        file_type = 'hiring_checklist'
                        role_name = file_key[len('hiring_checklist_'):].replace('_', ' ').title()
                    elif file_key.startswith('hiring_timeline_'):
                        file_type = 'hiring_timeline'
                        role_name = file_key[len('hiring_timeline_'):].replace('_', ' ').title()
                    elif file_key.startswith('salary_recommendation_'):
                        file_type = 'salary_recommendation'
                        role_name = file_key[len('salary_recommendation_'):].replace('_', ' ').title()
                    elif file_key.startswith('interview_questions_'):
                        file_type = 'interview_questions'
                        role_name = file_key[len('interview_questions_'):].replace('_', ' ').title()
                    else:
                        # Fallback to old logic
                        file_type = parts[0]
                        role_name = '_'.join(parts[1:]).replace('_', ' ').title()
                    
                    if role_name not in files_by_role:
                        files_by_role[role_name] = {}
                    files_by_role[role_name][file_type] = file_path
            
            # Display files by role
            # Define the desired order of document types
            document_order = [
                'job_description',
                'hiring_checklist', 
                'hiring_timeline',
                'interview_questions',
                'salary_recommendation'
            ]
            
            for role_name, role_files in files_by_role.items():
                st.subheader(f"📋 {role_name}")
                
                # Sort files by the desired order
                ordered_files = []
                for doc_type in document_order:
                    if doc_type in role_files:
                        ordered_files.append((doc_type, role_files[doc_type]))
                
                cols = st.columns(len(ordered_files))
                
                for i, (file_type, file_path) in enumerate(ordered_files):
                    with cols[i]:
                        file_type_display = file_type.replace('_', ' ').title()
                        st.write(f"**{file_type_display}**")
                        
                        # Try to read file content for download
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Download button with unique key
                            filename = os.path.basename(file_path)
                            unique_key = f"download_{role_name.lower().replace(' ', '_')}_{file_type}"
                            st.download_button(
                                label=f"📥 Download",
                                data=content,
                                file_name=filename,
                                mime="text/markdown",
                                key=unique_key
                            )
                                
                        except Exception as e:
                            st.error(f"Error reading file: {e}")
                
                # Add bulk download button for this role
                st.markdown("---")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    try:
                        zip_data = self.create_role_zip(role_name, role_files)
                        zip_filename = f"{role_name.lower().replace(' ', '_')}_hiring_materials.zip"
                        
                        st.download_button(
                            label=f"📦 Download All Files for {role_name}",
                            data=zip_data,
                            file_name=zip_filename,
                            mime="application/zip",
                            key=f"bulk_download_{role_name.lower().replace(' ', '_')}",
                            type="secondary"
                        )
                    except Exception as e:
                        st.error(f"Error creating ZIP file: {e}")
                
                st.divider()  # Add separation between roles
        
        # Option to start new session
        st.divider()
        if st.button("🆕 Plan Another Hiring Process", type="primary"):
            self.start_new_session()
    
    def run(self):
        """Run the Streamlit application."""
        # Check if setup is needed before rendering anything else
        if not st.session_state.setup_complete:
            self.render_setup_wizard()
            return
        
        self.render_header()
        
        # Main layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self.render_chat_interface()
        
        with col2:
            self.render_sidebar()


def validate_openai_api_key(api_key: str) -> bool:
    """Validate OpenAI API key by making a simple API call."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage
        
        # Create a simple test client
        test_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=api_key,
            max_tokens=5  # Very small to save costs
        )
        
        # Make a minimal test call
        response = test_llm.invoke([HumanMessage(content="Hi")])
        return True
        
    except Exception as e:
        error_str = str(e).lower()
        if "invalid api key" in error_str or "incorrect api key" in error_str or "authentication" in error_str:
            return False
        elif "quota" in error_str or "rate limit" in error_str:
            # API key is valid but has quota/rate issues - still valid key
            return True
        else:
            # Other errors (network, etc.) - assume key might be valid
            return True

def render_api_key_setup():
    """Render user-friendly API key setup interface."""
    # Header
    st.title("🤖 HR Assistant - Setup Required")
    st.markdown("---")
    
    # API Key setup section
    st.subheader("🔑 OpenAI API Key Setup")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        To use HR Assistant, you need a valid OpenAI API key. Here's how to set it up:
        
        ### Option 1: Environment File (Recommended)
        1. Create a `.env` file in your project root directory
        2. Add your API key: `OPENAI_API_KEY=your_key_here`
        3. Restart the application
        
        ### Option 2: Environment Variable
        Set the `OPENAI_API_KEY` environment variable on your system
        
        ### Get an API Key
        1. Go to [OpenAI's website](https://platform.openai.com/api-keys)
        2. Sign in or create an account
        3. Create a new API key
        4. Copy the key and add it using one of the methods above
        """)
        
        # Test API key input
        st.markdown("### Test Your API Key")
        api_key_input = st.text_input(
            "Enter your API key to test:",
            type="password",
            placeholder="sk-...",
            help="This will not be saved, only used for testing"
        )
        
        if st.button("Test API Key", disabled=not api_key_input):
            with st.spinner("Testing API key..."):
                if validate_openai_api_key(api_key_input):
                    st.success("✅ API key is valid! Please add it to your .env file and restart the app.")
                else:
                    st.error("❌ Invalid API key. Please check your key and try again.")
    
    with col2:
        st.info("""
        💡 **Tips:**
        
        - Keep your API key secure
        - Don't share it publicly
        - Monitor your usage at OpenAI
        - The app needs internet access
        """)
        
        st.markdown("---")
        
        st.markdown("""
        **Need Help?**
        
        - [OpenAI API Documentation](https://platform.openai.com/docs)
        - [API Key Management](https://platform.openai.com/api-keys)
        - [Pricing Information](https://openai.com/pricing)
        """)

# Main application entry point
def main():
    """Main function to run the Streamlit app."""
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        render_api_key_setup()
        return
    
    # Validate API key
    if not validate_openai_api_key(api_key):
        st.error("🔑 Invalid OpenAI API Key!")
        st.markdown("""
        Your OpenAI API key appears to be invalid. Please check:
        
        - The key is correctly formatted (starts with 'sk-')
        - The key hasn't expired
        - You have sufficient credits/quota
        - The key has the necessary permissions
        
        Please update your `.env` file with a valid API key and restart the application.
        """)
        
        # Also show the setup interface
        st.markdown("---")
        render_api_key_setup()
        return
    
    # Initialize and run the app
    app = HRAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
