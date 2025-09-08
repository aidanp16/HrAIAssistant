"""Interview questions generation tool for HR Assistant."""

import os
from typing import Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from config.prompts import INTERVIEW_QUESTIONS_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@tool
def generate_interview_questions(role_info: Dict[str, Any], company_info: Dict[str, Any]) -> str:
    """Generate comprehensive interview questions for a startup position."""
    
    prompt = INTERVIEW_QUESTIONS_PROMPT.format(
        company_name=company_info.get("name", "Our Company"),
        company_description=company_info.get("description", "An innovative company making a difference in our industry"),
        company_values=company_info.get("values", "Innovation, collaboration, and excellence"),
        company_mission=company_info.get("mission", "Building solutions that matter"),
        company_size=company_info.get("size", "Early-stage startup"),
        company_stage=company_info.get("stage", "Growing startup"),
        role_title=role_info.get("title", ""),
        seniority_level=role_info.get("seniority_level", "Mid-level"),
        department=role_info.get("department", ""),
        required_skills=", ".join(role_info.get("specific_skills", [])) if role_info.get("specific_skills") else "To be discussed",
        industry=company_info.get("industry", "Technology")
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        return f"""# Interview Questions: {role_info.get('title', 'Position')}

## Technical/Functional Skills
1. Walk me through your experience with [relevant technology/skill]
2. Describe a challenging technical problem you solved recently
3. How do you stay current with industry trends and best practices?
4. What's your approach to [role-specific task]?

## Startup Fit & Adaptability  
1. Tell me about a time you had to work with limited resources
2. How do you handle ambiguity and changing priorities?
3. Describe your experience working in fast-paced environments
4. What attracts you to working at a startup vs. a larger company?

## Leadership & Collaboration
1. Describe a time you had to influence without authority
2. How do you handle disagreements with team members?
3. Tell me about a project where you had to collaborate across departments
4. How do you mentor or support junior team members?

## Company Culture & Motivation
1. What motivates you in your work?
2. How do you define success in this role?
3. What questions do you have about our company culture?
4. Where do you see yourself growing within our organization?

## Closing Questions
1. What questions do you have for us?
2. What would make you excited to join our team?
3. Is there anything we haven't covered that you'd like us to know?

*Tailor these questions based on the specific role and candidate background*
"""


def save_interview_questions(content: str, role_title: str, output_dir: str = "output", session_id: str = None) -> str:
    """Save interview questions to a markdown file."""
    import os
    
    # Create session-specific subdirectory if session_id provided
    if session_id:
        session_output_dir = os.path.join(output_dir, session_id)
    else:
        session_output_dir = output_dir
    
    os.makedirs(session_output_dir, exist_ok=True)
    safe_title = "".join(c for c in role_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    filename = f"interview_questions_{safe_title}.md"
    filepath = os.path.join(session_output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Error saving interview questions: {e}")
        return ""
