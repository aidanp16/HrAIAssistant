"""Main LangGraph workflow for HR Assistant."""

import os
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ConversationState, WorkflowStage, create_initial_state
from .nodes import (
    initial_analysis_node,
    question_generation_node, 
    response_processing_node,
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
        self.checkpointer = MemorySaver()
        self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        
        # Create state graph
        workflow = StateGraph(ConversationState)
        
        # Add nodes
        workflow.add_node("initial_analysis", self._initial_analysis_wrapper)
        workflow.add_node("question_generation", self._question_generation_wrapper)
        workflow.add_node("response_processing", self._response_processing_wrapper)
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
                "question_generation": "question_generation",
                "content_generation_coordinator": "content_generation_coordinator"
            }
        )
        
        workflow.add_conditional_edges(
            "question_generation", 
            self._route_after_questions,
            {
                "wait_for_response": END,
                "content_generation_coordinator": "content_generation_coordinator"
            }
        )
        
        workflow.add_conditional_edges(
            "response_processing",
            self._route_after_response,
            {
                "question_generation": "question_generation",
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
    
    def _question_generation_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for question generation node.""" 
        return question_generation_node(state)
    
    def _response_processing_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for response processing node."""
        # This will be called with user response from the Streamlit frontend
        user_response = state.get("user_response", "")
        return response_processing_node(state, user_response)
    
    def _content_coordinator_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for content generation coordinator."""
        return content_generation_coordinator_node(state)
    
    def _content_generation_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Generate all content for all job roles."""
        generated_files = {}
        
        for role in state["job_roles"]:
            role_title = role["title"]
            company_info = state["company_info"]
            
            try:
                # Generate job description
                job_desc = generate_job_description(dict(role), dict(company_info))
                job_desc_path = save_job_description(job_desc, role_title)
                if job_desc_path:
                    generated_files[f"job_description_{role_title.lower().replace(' ', '_')}"] = job_desc_path
                
                # Generate hiring checklist
                checklist = generate_hiring_checklist(dict(role), dict(company_info))
                checklist_path = save_hiring_checklist(checklist, role_title)
                if checklist_path:
                    generated_files[f"hiring_checklist_{role_title.lower().replace(' ', '_')}"] = checklist_path
                
                # Generate hiring timeline
                timeline = generate_hiring_timeline(dict(role), dict(company_info))
                timeline_path = save_hiring_timeline(timeline, role_title)
                if timeline_path:
                    generated_files[f"hiring_timeline_{role_title.lower().replace(' ', '_')}"] = timeline_path
                
                # Generate salary recommendation
                salary_rec = generate_salary_recommendation(dict(role), dict(company_info))
                salary_path = save_salary_recommendation(salary_rec, role_title)
                if salary_path:
                    generated_files[f"salary_recommendation_{role_title.lower().replace(' ', '_')}"] = salary_path
                
                # Generate interview questions
                questions = generate_interview_questions(dict(role), dict(company_info))
                questions_path = save_interview_questions(questions, role_title)
                if questions_path:
                    generated_files[f"interview_questions_{role_title.lower().replace(' ', '_')}"] = questions_path
                    
            except Exception as e:
                print(f"Error generating content for {role_title}: {e}")
        
        return {
            "generated_files": generated_files,
            "stage": WorkflowStage.COMPLETED
        }
    
    def _completion_wrapper(self, state: ConversationState) -> Dict[str, Any]:
        """Wrapper for completion node."""
        return completion_node(state)
    
    def _route_after_analysis(self, state: ConversationState) -> str:
        """Route after initial analysis."""
        if state["stage"] == WorkflowStage.GENERATING_CONTENT:
            return "content_generation_coordinator"
        else:
            return "question_generation"
    
    def _route_after_questions(self, state: ConversationState) -> str:
        """Route after question generation."""
        if state.get("pending_user_response", False):
            return "wait_for_response"
        else:
            return "content_generation_coordinator"
    
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
            # Add user response to state
            updated_state = dict(current_state.values)
            updated_state["user_response"] = user_response
            updated_state["pending_user_response"] = False
            
            # Continue from response processing
            result = self.graph.invoke(
                updated_state, 
                config,
                start="response_processing"
            )
            
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
