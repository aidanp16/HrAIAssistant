"""Main LangGraph workflow for HR Assistant."""

import os
import sqlite3
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .state import ConversationState, WorkflowStage, create_initial_state
from .nodes import (
    initial_analysis_node,
    role_focus_node,
    question_generation_node, 
    response_processing_node,
    role_completion_check_node,
    content_generation_coordinator_node,
    completion_node,
    should_ask_questions,
    needs_user_response
)
from tools.job_description import generate_job_description, save_job_description
from tools.hiring_checklist import generate_hiring_checklist, save_hiring_checklist
from tools.hiring_timeline import generate_hiring_timeline, save_hiring_timeline
from tools.salary_recommendation import generate_salary_recommendation, save_salary_recommendation
from tools.interview_questions import generate_interview_questions, save_interview_questions


class HRAssistantWorkflow:
    """Main workflow orchestrator for HR Assistant."""
    
    def __init__(self):
        self.graph = None
        # Initialize persistent checkpointer with automatic database creation
        try:
            # Create SQLite connection and initialize checkpointer
            self.conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
            self.checkpointer = SqliteSaver(self.conn)
            # Setup the database schema
            self.checkpointer.setup()
        except Exception as e:
            print(f"Warning: Could not create persistent storage: {e}")
            print("This shouldn't happen, but falling back to memory-only storage...")
            # Import fallback
            from langgraph.checkpoint.memory import MemorySaver
            self.checkpointer = MemorySaver()
            self.conn = None
        self._build_graph()
    
    def cleanup(self):
        """Clean up resources, especially database connections."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        
        # Create state graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("initial_analysis", self._initial_analysis_wrapper)
        workflow.add_node("role_focus", self._role_focus_wrapper)
        workflow.add_node("question_generation", self._question_generation_wrapper)
        workflow.add_node("role_completion_check", self._role_completion_check_wrapper)
        workflow.add_node("content_generation_coordinator", self._content_coordinator_wrapper)
        workflow.add_node("content_generation", self._content_generation_wrapper)
        workflow.add_node("completion", self._completion_wrapper)
        
        # Set entry point
        workflow.set_entry_point("initial_analysis")
        
        # Add conditional routing
        workflow.add_conditional_edges(
            "initial_analysis",
            self._route_after_analysis,
            {
                "role_focus": "role_focus",
                "content_generation_coordinator": "content_generation_coordinator"
            }
        )
        
        workflow.add_edge("role_focus", "question_generation")
        
        workflow.add_conditional_edges(
            "question_generation", 
            self._route_after_questions,
            {
                "wait_for_response": END,
                "role_completion_check": "role_completion_check"
            }
        )
        
        workflow.add_conditional_edges(
            "role_completion_check",
            self._route_after_role_check,
            {
                "role_focus": "role_focus",
                "content_generation_coordinator": "content_generation_coordinator"
            }
        )
        
        workflow.add_edge("content_generation_coordinator", "content_generation")
        workflow.add_edge("content_generation", "completion")
        workflow.add_edge("completion", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
    
    def _initial_analysis_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for initial analysis node."""
        return initial_analysis_node(state)
    
    def _role_focus_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for role focus node."""
        return role_focus_node(state)
    
    def _question_generation_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for question generation node.""" 
        return question_generation_node(state)
    
    def _role_completion_check_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for role completion check node."""
        return role_completion_check_node(state)
    
    def _response_processing_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for response processing node."""
        # This will be called with user response from the Streamlit frontend
        user_response = state.get("user_response", "")
        return response_processing_node(state, user_response)
    
    def _content_coordinator_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for content generation coordinator."""
        return content_generation_coordinator_node(state)
    
    def _generate_single_document(self, tool_func, save_func, doc_type, role, company_info, session_id):
        """Generate a single document for a role."""
        try:
            role_title = role["title"]
            content = tool_func.invoke({"role_info": dict(role), "company_info": dict(company_info)})
            # Pass session_id to save function for session-specific storage
            file_path = save_func(content, role_title, session_id=session_id)
            if file_path:
                file_key = f"{doc_type}_{role_title.lower().replace(' ', '_')}"
                return (file_key, file_path)
            return None
        except Exception as e:
            print(f"Error generating {doc_type} for {role['title']}: {e}")
            return None
    
    def _content_generation_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Generate all content for all job roles in parallel."""
        generated_files = {}
        
        # Load the complete company profile to ensure we have all available data
        try:
            from .company_profile import get_company_info_dict
        except ImportError:
            from src.company_profile import get_company_info_dict
        full_company_profile = get_company_info_dict()
        
        # Define all document generation tasks
        generation_tasks = []
        
        for role in state["job_roles"]:
            # Use full company profile instead of just state company_info
            # This ensures we get description, values, mission, etc.
            company_info = dict(full_company_profile)
            
            # Add role-specific budget and timeline to company info
            company_info["budget_range"] = role.get("budget_range", "Competitive")
            company_info["timeline"] = role.get("timeline", "Standard timeline")
            
            # Add all document types for this role
            generation_tasks.extend([
                (generate_job_description, save_job_description, "job_description", role, company_info),
                (generate_hiring_checklist, save_hiring_checklist, "hiring_checklist", role, company_info),
                (generate_hiring_timeline, save_hiring_timeline, "hiring_timeline", role, company_info),
                (generate_salary_recommendation, save_salary_recommendation, "salary_recommendation", role, company_info),
                (generate_interview_questions, save_interview_questions, "interview_questions", role, company_info)
            ])
        
        # Get session_id from state
        session_id = state["session_id"]
        
        # Execute all tasks in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all tasks with session_id
            future_to_task = {
                executor.submit(self._generate_single_document, *task, session_id): task 
                for task in generation_tasks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                result = future.result()
                if result:
                    file_key, file_path = result
                    generated_files[file_key] = file_path
        
        return {
            "generated_files": generated_files,
            "stage": WorkflowStage.COMPLETED
        }
    
    def _completion_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for completion node."""
        return completion_node(state)
    
    def _route_after_analysis(self, state: ConversationState) -> str:
        """Route after initial analysis."""
        if state.get("ready_for_generation", False):
            # All information complete from initial analysis, go straight to coordinator for confirmation
            return "content_generation_coordinator"
        elif state["stage"] == WorkflowStage.GENERATING_CONTENT:
            return "content_generation_coordinator"
        else:
            return "role_focus"
    
    def _route_after_questions(self, state: ConversationState) -> str:
        """Route after question generation."""
        if state.get("pending_user_response", False):
            return "wait_for_response"
        else:
            return "role_completion_check"
    
    def _route_after_role_check(self, state: ConversationState) -> str:
        """Route after role completion check."""
        if state["stage"] == WorkflowStage.GENERATING_CONTENT:
            return "content_generation_coordinator"
        else:
            return "role_focus"
    
    def _route_after_response(self, state: ConversationState) -> str:
        """Route after processing user response."""
        if state["stage"] == WorkflowStage.GENERATING_CONTENT:
            return "content_generation_coordinator"
        else:
            return "question_generation"
    
    def start_conversation(self, user_request: str, session_id: str) -> ConversationState:
        """Start a new conversation."""
        initial_state = create_initial_state(user_request, session_id)
        
        # Run initial analysis
        config = {"configurable": {"thread_id": session_id}}
        result = self.graph.invoke(initial_state, config)
        
        return result
    
    def continue_conversation(self, user_response: str, session_id: str) -> ConversationState:
        """Continue an existing conversation with user response."""
        config = {"configurable": {"thread_id": session_id}}
        
        # Get current state
        current_state = self.graph.get_state(config)
        
        if current_state and current_state.values:
            try:
                # Process the response directly
                from .nodes import response_processing_node
                
                # Add user response to current state
                updated_state = dict(current_state.values)
                updated_state["user_response"] = user_response
                
                # Process the response
                response_result = response_processing_node(updated_state, user_response)
                
                # Update state with processed response
                for key, value in response_result.items():
                    updated_state[key] = value
                
                # Process role completion check after user response
                role_check_result = role_completion_check_node(updated_state)
                for key, value in role_check_result.items():
                    updated_state[key] = value
            except Exception as e:
                import traceback
                traceback.print_exc()
                return updated_state if 'updated_state' in locals() else current_state.values
            
            # Continue workflow based on role check result
            if updated_state.get("ready_for_generation", False):
                # All roles complete, go to content generation
                from .nodes import content_generation_coordinator_node
                coordinator_result = content_generation_coordinator_node(updated_state)
                for key, value in coordinator_result.items():
                    updated_state[key] = value
                
                # Generate all content
                content_result = self._content_generation_wrapper(updated_state)
                for key, value in content_result.items():
                    updated_state[key] = value
                
                # Mark as completed
                completion_result = self._completion_wrapper(updated_state)
                for key, value in completion_result.items():
                    updated_state[key] = value
                
                result = updated_state
            else:
                # Need more info for current role or move to next role
                # Check if we moved to a new role after role completion check
                old_role_index = current_state.values.get("current_role_index", 0)
                new_role_index = updated_state.get("current_role_index", 0)
                moved_to_new_role = new_role_index > old_role_index
                
                # Only call role_focus_node if we actually moved to a new role
                if moved_to_new_role:
                    role_focus_result = role_focus_node(updated_state)
                    for key, value in role_focus_result.items():
                        updated_state[key] = value
                
                # Check if we're ready for content generation
                if updated_state.get("ready_for_generation", False) or updated_state.get("stage") == WorkflowStage.GENERATING_CONTENT:
                    # All roles complete, go to content generation
                    from .nodes import content_generation_coordinator_node
                    coordinator_result = content_generation_coordinator_node(updated_state)
                    for key, value in coordinator_result.items():
                        updated_state[key] = value
                    
                    # Generate all content
                    content_result = self._content_generation_wrapper(updated_state)
                    for key, value in content_result.items():
                        updated_state[key] = value
                    
                    # Mark as completed
                    completion_result = self._completion_wrapper(updated_state)
                    for key, value in completion_result.items():
                        updated_state[key] = value
                elif updated_state.get("stage") == WorkflowStage.ASKING_QUESTIONS:
                    # Still need more info for current role, generate questions
                    question_result = question_generation_node(updated_state)
                    for key, value in question_result.items():
                        updated_state[key] = value
                
                result = updated_state
            
            return result
        else:
            # No existing state, start new conversation
            return self.start_conversation(user_response, session_id)
    
    def get_conversation_state(self, session_id: str) -> ConversationState:
        """Get current conversation state."""
        config = {"configurable": {"thread_id": session_id}}
        state = self.graph.get_state(config)
        
        if state and state.values:
            return state.values
        else:
            return None
    
    def list_generated_files(self, session_id: str) -> List[str]:
        """Get list of generated files for a session."""
        state = self.get_conversation_state(session_id)
        if state and "generated_files" in state:
            return list(state["generated_files"].values())
        return []


# Global workflow instance
hr_workflow = HRAssistantWorkflow()
