"""LangGraph workflow nodes for HR Assistant."""

import json
import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from .state import (
    ConversationState, WorkflowStage, JobRole, 
    is_information_sufficient, get_missing_information,
    is_role_information_sufficient, get_missing_information_for_role,
    get_current_role, are_all_roles_complete
)
from config.prompts import (
    INITIAL_ANALYSIS_PROMPT,
    QUESTION_GENERATION_PROMPT, 
    RESPONSE_PROCESSING_PROMPT
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


def initial_analysis_node(state: ConversationState) -> Dict[str, Any]:
    """
    Analyze the initial user request to extract job roles and company information.
    """
    prompt = INITIAL_ANALYSIS_PROMPT.format(
        original_request=state["original_request"]
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Clean the response content to ensure valid JSON
        content = response.content.strip()
        
        # Try to extract JSON if there's extra text
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        if content.startswith('```'):
            content = content[3:]
        
        content = content.strip()
        
        if not content:
            raise ValueError("Empty response from GPT")
            
        analysis = json.loads(content)
        
        # Extract job roles
        job_roles = []
        for role_data in analysis.get("job_roles", []):
            job_role = JobRole(
                title=role_data["title"],
                seniority_level=role_data.get("seniority_level"),
                department=role_data.get("department"),
                specific_skills=role_data.get("specific_skills"),
                budget_range=None,  # Will be filled in by response processing
                timeline=None,      # Will be filled in by response processing
                generated_content=None
            )
            job_roles.append(job_role)
        
        # Update company info with any provided details
        company_updates = analysis.get("company_info_provided", {})
        updated_company = dict(state["company_info"])
        for key, value in company_updates.items():
            if value is not None:
                updated_company[key] = value
        
        # Initialize role completion tracking
        role_completion_status = [False] * len(job_roles)
        
        # Update conversation state
        updates = {
            "job_roles": job_roles,
            "company_info": updated_company,
            "current_role_index": 0,
            "role_completion_status": role_completion_status,
            "stage": WorkflowStage.ASKING_QUESTIONS if analysis.get("needs_more_info", True) else WorkflowStage.GENERATING_CONTENT,
            "messages": state["messages"] + [
                {"role": "user", "content": state["original_request"]}
            ]
        }
        
        return updates
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error in initial analysis: {e}")
        print(f"Content that failed to parse: '{content}'")
        return _get_initial_analysis_fallback(state)
    except Exception as e:
        print(f"General error in initial analysis: {e}")
        return _get_initial_analysis_fallback(state)


def question_generation_node(state: ConversationState) -> Dict[str, Any]:
    """
    Generate contextual questions for the current role only.
    """
    current_role = get_current_role(state)
    current_index = state.get("current_role_index", 0)
    
    if not current_role:
        # No current role, shouldn't happen but handle gracefully
        return {
            "stage": WorkflowStage.GENERATING_CONTENT,
            "ready_for_generation": True
        }
    
    missing_info = get_missing_information_for_role(current_role)
    
    prompt = QUESTION_GENERATION_PROMPT.format(
        original_request=state["original_request"],
        current_role=json.dumps(dict(current_role), indent=2),
        current_role_title=current_role["title"],
        company_info=json.dumps(dict(state["company_info"]), indent=2),
        missing_info=json.dumps(missing_info, indent=2)
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Clean the response content to ensure valid JSON
        content = response.content.strip()
        
        # Try to extract JSON if there's extra text
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        if content.startswith('```'):
            content = content[3:]
        
        content = content.strip()
        
        if not content:
            raise ValueError("Empty response from GPT")
            
        questions = json.loads(content)
        
        role_title = current_role["title"]
        return {
            "current_questions": questions,
            "pending_user_response": True,
            "missing_info": missing_info,
            "messages": state["messages"] + [
                {"role": "assistant", "content": f"I need some more details about the **{role_title}** role to create the best hiring materials:\n\n" + 
                 "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])}
            ]
        }
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error in question generation: {e}")
        print(f"Content that failed to parse: '{content}'")
        return _get_question_generation_fallback(state, missing_info)
    except Exception as e:
        print(f"General error generating questions: {e}")
        return _get_question_generation_fallback(state, missing_info)


def response_processing_node(state: ConversationState, user_response: str) -> Dict[str, Any]:
    """
    Process user's response to questions and update the state.
    """
    prompt = RESPONSE_PROCESSING_PROMPT.format(
        questions=json.dumps(state.get("current_questions", []), indent=2),
        user_response=user_response,
        company_info=json.dumps(dict(state["company_info"]), indent=2),
        job_roles=json.dumps([dict(role) for role in state["job_roles"]], indent=2)
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Clean the response content to ensure valid JSON
        content = response.content.strip()
        
        # Try to extract JSON if there's extra text
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        content = content.strip()
        
        updates_data = json.loads(content)
        
        # Update company info
        company_info = dict(state["company_info"])
        company_updates = updates_data.get("company_info_updates", {})
        for key, value in company_updates.items():
            if value is not None:
                company_info[key] = value
        
        # Update only the current role
        job_roles = list(state["job_roles"])
        current_index = state.get("current_role_index", 0)
        
        # Apply updates to current role only
        for role_update in updates_data.get("job_role_updates", []):
            update_index = role_update.get("index", 0)
            role_updates = role_update.get("updates", {})
            
            # Apply updates to the specified role index if it's valid and has meaningful data
            if update_index < len(job_roles) and any(v is not None for v in role_updates.values()):
                for key, value in role_updates.items():
                    if value is not None:
                        job_roles[update_index][key] = value
        
        # Add any additional roles
        for new_role_data in updates_data.get("additional_roles", []):
            new_role = JobRole(
                title=new_role_data["title"],
                seniority_level=new_role_data.get("seniority_level"),
                department=new_role_data.get("department"),
                specific_skills=new_role_data.get("specific_skills"),
                budget_range=new_role_data.get("budget_range"),
                timeline=new_role_data.get("timeline"),
                generated_content=None
            )
            job_roles.append(new_role)
        
        # Update state - PRESERVE all existing state values
        result = {
            "company_info": company_info,
            "job_roles": job_roles,
            "pending_user_response": False,
            "current_questions": None,
            # CRITICAL: Preserve existing state values
            "current_role_index": state.get("current_role_index", 0),
            "role_completion_status": state.get("role_completion_status", []),
            "messages": state["messages"] + [
                {"role": "user", "content": user_response},
                {"role": "assistant", "content": "Thanks for the information!"}
            ]
        }
        
        # Always move to role completion check after processing response
        result["stage"] = WorkflowStage.ASKING_QUESTIONS
        
        return result
        
    except Exception as e:
        print(f"Error processing response: {e}")
        # If JSON parsing fails, acknowledge the response but continue with role completion check
        result = {
            "pending_user_response": False,
            "current_questions": None,
            # CRITICAL: Preserve existing state values even in fallback
            "current_role_index": state.get("current_role_index", 0),
            "role_completion_status": state.get("role_completion_status", []),
            "messages": state["messages"] + [
                {"role": "user", "content": user_response},
                {"role": "assistant", "content": "Thanks for that information!"}
            ],
            "stage": WorkflowStage.ASKING_QUESTIONS
        }
        
        return result


def content_generation_coordinator_node(state: ConversationState) -> Dict[str, Any]:
    """
    Coordinate the generation of all content types for each job role.
    """
    content_types = [
        "job_description",
        "hiring_checklist", 
        "hiring_timeline",
        "salary_recommendation",
        "interview_questions"
    ]
    
    content_to_generate = []
    for role in state["job_roles"]:
        for content_type in content_types:
            content_to_generate.append(f"{role['title']}_{content_type}")
    
    return {
        "stage": WorkflowStage.GENERATING_CONTENT,
        "content_to_generate": content_to_generate,
        "ready_for_generation": True,
        "messages": state["messages"] + [
            {"role": "assistant", "content": f"Perfect! I have enough information to create comprehensive hiring materials for your {len(state['job_roles'])} role(s). I'll generate job descriptions, hiring checklists, timelines, salary recommendations, and interview questions for each position."}
        ]
    }


def completion_node(state: ConversationState) -> Dict[str, Any]:
    """
    Mark the workflow as completed and provide summary.
    """
    total_files = len(state.get("generated_files", {}))
    roles_count = len(state["job_roles"])
    
    summary_message = f"""
🎉 **Hiring Plan Complete!**

I've successfully created comprehensive hiring materials for your {roles_count} role(s):

**Generated Materials:**
- {total_files} files total
- Job descriptions for each role
- Hiring checklists and timelines
- Salary recommendations
- Interview question sets

All files have been saved as markdown documents and are ready for use. Good luck with your hiring process! 🚀
    """.strip()
    
    return {
        "stage": WorkflowStage.COMPLETED,
        "messages": state["messages"] + [
            {"role": "assistant", "content": summary_message}
        ]
    }


# Routing functions for conditional logic
def should_ask_questions(state: ConversationState) -> str:
    """Determine if we need to ask more questions or can proceed to generation."""
    if state["stage"] == WorkflowStage.INITIAL_ANALYSIS:
        return "question_generation"
    elif state["stage"] == WorkflowStage.ASKING_QUESTIONS:
        if is_information_sufficient(state):
            return "content_generation_coordinator"
        else:
            return "question_generation"
    elif state["stage"] == WorkflowStage.GENERATING_CONTENT:
        return "content_generation"
    elif state["stage"] == WorkflowStage.COMPLETED:
        return "completion"
    else:
        return "question_generation"


def needs_user_response(state: ConversationState) -> bool:
    """Check if we're waiting for user response."""
    return state.get("pending_user_response", False)


# Helper functions for fallback handling
def _get_initial_analysis_fallback(state: ConversationState) -> Dict[str, Any]:
    """Fallback response for initial analysis failures."""
    # Since we can't parse the GPT response, we'll create a generic job role
    # to allow the process to continue
    fallback_role = JobRole(
        title="Position",  # Generic title that will be refined later
        seniority_level=None,
        department=None,
        specific_skills=None,
        budget_range=None,
        timeline=None,
        generated_content=None
    )
    
    return {
        "stage": WorkflowStage.ASKING_QUESTIONS,
        "job_roles": [fallback_role],  # Provide at least one role so workflow can continue
        "messages": state["messages"] + [
            {"role": "user", "content": state["original_request"]},
            {"role": "assistant", "content": "I'll help you with your hiring needs. Let me ask a few questions to get started."}
        ]
    }


def role_focus_node(state: ConversationState) -> Dict[str, Any]:
    """Set up focus on the current role and introduce it to the user."""
    current_role = get_current_role(state)
    current_index = state.get("current_role_index", 0)
    job_roles = state.get("job_roles", [])
    
    if not current_role or current_index >= len(job_roles):
        # All roles complete, move to content generation
        return {
            "stage": WorkflowStage.GENERATING_CONTENT,
            "ready_for_generation": True
        }
    
    role_title = current_role["title"]
    total_roles = len(state["job_roles"])
    completion_status = state.get("role_completion_status", [])
    
    if current_index == 0:
        # First role introduction
        intro_message = f"Great! I found {total_roles} role(s) to help you with. Let's start with the **{role_title}** position and gather the details I need to create comprehensive hiring materials."
    else:
        # Subsequent role introduction
        intro_message = f"Perfect! I have enough information about the previous role. Now let's focus on the **{role_title}** position."
    
    return {
        "stage": WorkflowStage.ASKING_QUESTIONS,
        "messages": state["messages"] + [
            {"role": "assistant", "content": intro_message}
        ]
    }


def role_completion_check_node(state: ConversationState) -> Dict[str, Any]:
    """Check if current role is complete and determine next steps."""
    current_role = get_current_role(state)
    current_index = state.get("current_role_index", 0)
    job_roles = state.get("job_roles", [])
    completion_status = list(state.get("role_completion_status", []))
    
    if not current_role or current_index >= len(job_roles):
        # No current role or index out of bounds, move to content generation
        return {
            "stage": WorkflowStage.GENERATING_CONTENT,
            "ready_for_generation": True
        }
    
    role_complete = is_role_information_sufficient(current_role)
    
    # Ensure completion status list is the right length
    while len(completion_status) < len(job_roles):
        completion_status.append(False)
    
    if role_complete:
        # Mark current role as complete
        completion_status[current_index] = True
        role_title = current_role["title"]
        
        # Check if there are more roles to process
        next_index = current_index + 1
        
        if next_index < len(job_roles):
            # Move to next role - increment index and stay in ASKING_QUESTIONS stage
            next_role_title = job_roles[next_index]["title"]
            result = {
                "current_role_index": next_index,
                "role_completion_status": completion_status,
                "stage": WorkflowStage.ASKING_QUESTIONS,
                "messages": state["messages"] + [
                    {"role": "assistant", "content": f"Excellent! I have enough information about the **{role_title}** role."}
                ]
            }
            return result
        else:
            # All roles complete, move to content generation
            result = {
                "role_completion_status": completion_status,
                "stage": WorkflowStage.GENERATING_CONTENT,
                "ready_for_generation": True
            }
            return result
    else:
        # Role not complete, continue asking questions for current role
        completion_status[current_index] = False
        result = {
            "role_completion_status": completion_status,
            "stage": WorkflowStage.ASKING_QUESTIONS
        }
        return result


def _get_question_generation_fallback(state: ConversationState, missing_info: List[str]) -> Dict[str, Any]:
    """Fallback response for question generation failures."""
    current_role = get_current_role(state)
    role_title = current_role["title"] if current_role else "this position"
    
    # Use basic fallback questions when JSON parsing fails
    fallback_questions = [
        f"What's your budget range for the {role_title}?",
        f"How quickly do you need to fill the {role_title} role?",
        f"What are the key skills required for the {role_title}?"
    ]
    
    return {
        "current_questions": fallback_questions,
        "pending_user_response": True,
        "missing_info": missing_info,
        "messages": state["messages"] + [
            {"role": "assistant", "content": f"I need some more information about the {role_title} role:\n\n" + 
             "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])}
        ]
    }
