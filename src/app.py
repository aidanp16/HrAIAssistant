"""Streamlit frontend application for HR Assistant."""

import streamlit as st
import os
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
except ImportError:
    # For running directly
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from src.workflow import hr_workflow
    from src.session_manager import session_manager
    from src.state import WorkflowStage


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
    
    def render_header(self):
        """Render the application header."""
        st.title("🤖 HR Assistant - AI Hiring Planner")
        st.markdown("""
        Welcome to your intelligent hiring assistant! I help startups create comprehensive hiring plans.
        Just tell me what roles you need to fill, and I'll guide you through creating:
        
        📋 **Job Descriptions** • ✅ **Hiring Checklists** • ⏰ **Timelines** • 💰 **Salary Recommendations** • ❓ **Interview Questions**
        """)
        st.divider()
    
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
            
            # App info
            st.header("ℹ️ About")
            st.markdown("""
            **HR Assistant** uses:
            - 🧠 **GPT-5-mini** for intelligent content generation
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
        st.session_state.messages = []
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
        
        # Display conversation history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Initial prompt or continue conversation
        if not st.session_state.conversation_started:
            self.render_initial_input()
        else:
            self.render_conversation_continuation()
    
    def render_initial_input(self):
        """Render initial hiring request input."""
        st.subheader("🚀 What hiring help do you need?")
        
        # Example prompts
        st.markdown("**Try these examples:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💻 Technical Roles"):
                example = "I need to hire a senior software engineer and a DevOps engineer"
                self.start_conversation(example)
        
        with col2:
            if st.button("🚀 Founding Team"):
                example = "I need to hire a founding engineer and a GenAI intern"
                self.start_conversation(example)
                
        with col3:
            if st.button("📈 Growth Roles"):
                example = "I need to hire a product manager and a marketing specialist"
                self.start_conversation(example)
        
        st.divider()
        
        # Custom input
        with st.container():
            user_input = st.text_area(
                "Describe your hiring needs:",
                placeholder="Example: I need to hire a senior frontend developer and a junior designer for my early-stage SaaS startup...",
                height=100,
                key="initial_input"
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Start Planning 🚀", type="primary", disabled=not user_input.strip()):
                    if user_input.strip():
                        self.start_conversation(user_input.strip())
    
    def start_conversation(self, user_request: str):
        """Start a new conversation with the user's request."""
        try:
            with st.spinner("Analyzing your hiring needs..."):
                # Start workflow
                result = hr_workflow.start_conversation(user_request, st.session_state.session_id)
                
                # Update session state
                st.session_state.current_state = result
                st.session_state.conversation_started = True
                st.session_state.messages = result.get("messages", [])
                
                # Save session
                session_manager.save_session(st.session_state.session_id, result)
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Error starting conversation: {e}")
            st.write("Please check your OpenAI API key and try again.")
    
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
        user_response = st.text_area(
            "Your response:",
            placeholder="Please answer the questions above with as much detail as possible...",
            height=100,
            key="response_input"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Submit Response 📤", type="primary", disabled=not user_response.strip()):
                if user_response.strip():
                    self.continue_conversation(user_response.strip())
    
    def continue_conversation(self, user_response: str):
        """Continue the conversation with user response."""
        try:
            with st.spinner("Processing your response..."):
                # Continue workflow
                result = hr_workflow.continue_conversation(user_response, st.session_state.session_id)
                
                # Update session state
                st.session_state.current_state = result
                st.session_state.messages = result.get("messages", [])
                
                # Save session
                session_manager.save_session(st.session_state.session_id, result)
                
                st.rerun()
                
        except Exception as e:
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
                # The workflow will automatically proceed to completion
                st.rerun()
    
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
                            st.write(f"**Skills:** {', '.join(skills)}")
        
        # Company information
        company_info = state.get("company_info", {})
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
                if company_info.get("budget_range"):
                    st.write(f"**Budget:** {company_info['budget_range']}")
                if company_info.get("timeline"):
                    st.write(f"**Timeline:** {company_info['timeline']}")
    
    def render_completion_interface(self):
        """Render completion interface with generated files."""
        st.balloons()
        st.success("🎉 Your hiring plan is complete!")
        
        state = st.session_state.current_state
        generated_files = state.get("generated_files", {})
        
        if generated_files:
            st.subheader("📁 Generated Materials")
            
            # Organize files by role
            files_by_role = {}
            for file_key, file_path in generated_files.items():
                # Extract role from filename
                parts = file_key.split('_', 2)
                if len(parts) >= 3:
                    file_type = parts[0]
                    role_name = parts[2].replace('_', ' ').title()
                    
                    if role_name not in files_by_role:
                        files_by_role[role_name] = {}
                    files_by_role[role_name][file_type] = file_path
            
            # Display files by role
            for role_name, role_files in files_by_role.items():
                with st.expander(f"📋 {role_name}", expanded=True):
                    cols = st.columns(len(role_files))
                    
                    for i, (file_type, file_path) in enumerate(role_files.items()):
                        with cols[i]:
                            file_type_display = file_type.replace('_', ' ').title()
                            st.write(f"**{file_type_display}**")
                            
                            # Try to read and display file content
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                
                                # Download button
                                filename = os.path.basename(file_path)
                                st.download_button(
                                    label=f"📥 Download",
                                    data=content,
                                    file_name=filename,
                                    mime="text/markdown",
                                    key=f"download_{file_key}"
                                )
                                
                                # Show preview
                                with st.expander("Preview", expanded=False):
                                    st.markdown(content[:500] + "..." if len(content) > 500 else content)
                                    
                            except Exception as e:
                                st.error(f"Error reading file: {e}")
            
            # Bulk download option
            st.divider()
            if st.button("📦 Download All Files", type="secondary"):
                st.info("Individual downloads available above. Bulk download feature coming soon!")
        
        # Option to start new session
        st.divider()
        if st.button("🆕 Plan Another Hiring Process", type="primary"):
            self.start_new_session()
    
    def run(self):
        """Run the Streamlit application."""
        self.render_header()
        
        # Main layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self.render_chat_interface()
        
        with col2:
            self.render_sidebar()


# Main application entry point
def main():
    """Main function to run the Streamlit app."""
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error("🔑 OpenAI API key not found!")
        st.markdown("""
        Please set your OpenAI API key:
        
        1. Create a `.env` file in the project root
        2. Add your API key: `OPENAI_API_KEY=your_key_here`
        3. Restart the application
        
        Or set it as an environment variable.
        """)
        st.stop()
    
    # Initialize and run the app
    app = HRAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
