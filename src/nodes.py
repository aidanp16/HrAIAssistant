"""LangGraph workflow nodes for HR Assistant."""

import json
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from .state import ConversationState, WorkflowStage, JobRole, is_information_sufficient, get_missing_information
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
        analysis = json.loads(response.content)
        
        # Extract job roles
        job_roles = []
        for role_data in analysis.get("job_roles", []):
            job_role = JobRole(
                title=role_data["title"],
                seniority_level=role_data.get("seniority_level"),
                department=role_data.get("department"),
                specific_skills=role_data.get("specific_skills"),
                generated_content=None
            )
            job_roles.append(job_role)
        
        # Update company info with any provided details
        company_updates = analysis.get("company_info_provided", {})
        updated_company = dict(state["company_info"])
        for key, value in company_updates.items():
            if value is not None:
                updated_company[key] = value
        
        # Update conversation state
        updates = {
            "job_roles": job_roles,
            "company_info": updated_company,
            "stage": WorkflowStage.ASKING_QUESTIONS if analysis.get("needs_more_info", True) else WorkflowStage.GENERATING_CONTENT,
            "messages": state["messages"] + [
                {"role": "user", "content": state["original_request"]},
                {"role": "assistant", "content": f"I found {len(job_roles)} role(s) to help you with: {', '.join([role['title'] for role in job_roles])}"}
            ]
        }
        
        return updates
        
    except Exception as e:
        print(f"Error in initial analysis: {e}")
        return {
            "stage": WorkflowStage.ASKING_QUESTIONS,
            "messages": state["messages"] + [
                {"role": "user", "content": state["original_request"]},
                {"role": "assistant", "content": "I'll help you with your hiring needs. Let me ask a few questions to get started."}
            ]
        }


def question_generation_node(state: ConversationState) -> Dict[str, Any]:
    """
    Generate contextual questions based on missing information.
    """
    missing_info = get_missing_information(state)
    
    prompt = QUESTION_GENERATION_PROMPT.format(
        original_request=state["original_request"],
        job_roles=json.dumps([dict(role) for role in state["job_roles"]], indent=2),
        company_info=json.dumps(dict(state["company_info"]), indent=2),
        missing_info=json.dumps(missing_info, indent=2)
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        questions = json.loads(response.content)
        
        return {
            "current_questions": questions,
            "pending_user_response": True,
            "missing_info": missing_info,
            "messages": state["messages"] + [
                {"role": "assistant", "content": f"I need some more information to create the best hiring materials for you. Here are a few questions:\n\n" + 
                 "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])}
            ]
        }
        
    except Exception as e:
        print(f"Error generating questions: {e}")
        # Fallback questions
        fallback_questions = [
            "What's your company size and current funding stage?",
            "What's your budget range for these roles?",
            "How quickly do you need to fill these positions?"
        ]
        return {
            "current_questions": fallback_questions,
            "pending_user_response": True,
            "missing_info": missing_info,
            "messages": state["messages"] + [
                {"role": "assistant", "content": f"I need some more information:\n\n" + 
                 "\n".join([f"{i+1}. {q}" for i, q in enumerate(fallback_questions)])}
            ]
        }


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
        print(f"GPT Response: {response.content}")
        
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
        
        # Update job roles
        job_roles = list(state["job_roles"])
        for role_update in updates_data.get("job_role_updates", []):
            index = role_update.get("index", 0)
            if 0 <= index < len(job_roles):
                role_updates = role_update.get("updates", {})
                for key, value in role_updates.items():
                    if value is not None:
                        job_roles[index][key] = value
        
        # Add any additional roles
        for new_role_data in updates_data.get("additional_roles", []):
            new_role = JobRole(
                title=new_role_data["title"],
                seniority_level=new_role_data.get("seniority_level"),
                department=new_role_data.get("department"),
                specific_skills=new_role_data.get("specific_skills"),
                generated_content=None
            )
            job_roles.append(new_role)
        
        # Update state
        result = {
            "company_info": company_info,
            "job_roles": job_roles,
            "pending_user_response": False,
            "current_questions": None,
            "messages": state["messages"] + [
                {"role": "user", "content": user_response},
                {"role": "assistant", "content": "Thanks for the information! Let me check if I need anything else."}
            ]
        }
        
        # Check if we have enough information
        temp_state = dict(state)
        temp_state.update(result)
        
        if is_information_sufficient(temp_state):
            result["stage"] = WorkflowStage.GENERATING_CONTENT
            result["ready_for_generation"] = True
        else:
            result["stage"] = WorkflowStage.ASKING_QUESTIONS
        
        return result
        
    except Exception as e:
        print(f"Error processing response: {e}")
        # If JSON parsing fails, acknowledge the response but mark as needing more info
        result = {
            "pending_user_response": False,
            "current_questions": None,
            "messages": state["messages"] + [
                {"role": "user", "content": user_response},
                {"role": "assistant", "content": "Thanks for that information! Let me see if I need any additional details to create the best hiring materials for you."}
            ]
        }
        
        # Check if we have enough information with current state
        if is_information_sufficient(state):
            result["stage"] = WorkflowStage.GENERATING_CONTENT
            result["ready_for_generation"] = True
        else:
            result["stage"] = WorkflowStage.ASKING_QUESTIONS
        
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
