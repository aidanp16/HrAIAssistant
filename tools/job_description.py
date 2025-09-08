"""Job description generation tool for HR Assistant."""

import os
from typing import Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from config.prompts import JOB_DESCRIPTION_PROMPT

load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@tool
def generate_job_description(role_info: Dict[str, Any], company_info: Dict[str, Any]) -> str:
    """
    Generate a comprehensive job description for a startup position.
    
    Args:
        role_info: Dictionary containing job role information
        company_info: Dictionary containing company information
    
    Returns:
        Generated job description as markdown string
    """
    
    # Format the prompt with available information
    prompt = JOB_DESCRIPTION_PROMPT.format(
        company_name=company_info.get("name", "Our Company"),
        company_description=company_info.get("description", "An innovative company making a difference in our industry"),
        company_values=company_info.get("values", "Innovation, collaboration, and excellence"),
        company_mission=company_info.get("mission", "Building solutions that matter"),
        company_size=company_info.get("size", "Early-stage startup"),
        company_stage=company_info.get("stage", "Growing startup"),
        industry=company_info.get("industry", "Technology"),
        location=company_info.get("location", "Remote-friendly"),
        remote_policy=company_info.get("remote_policy", "Flexible"),
        role_title=role_info.get("title", ""),
        seniority_level=role_info.get("seniority_level", "Mid-level"),
        department=role_info.get("department", ""),
        required_skills=", ".join(role_info.get("specific_skills", [])) if role_info.get("specific_skills") else "To be discussed",
        budget_range=company_info.get("budget_range", "Competitive")
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    except Exception as e:
        print(f"Error generating job description: {e}")
        # Return a basic fallback job description
        return f"""# {role_info.get('title', 'Job Position')}

## About the Role
We are looking for a talented {role_info.get('title', 'professional')} to join our {company_info.get('stage', 'growing')} team.

## Key Responsibilities
- Drive key initiatives and projects
- Collaborate with cross-functional teams
- Contribute to company growth and success

## Requirements
- Relevant experience in the field
- Strong problem-solving skills
- Startup mindset and adaptability

## What We Offer
- Competitive compensation and equity
- Flexible working arrangements
- Growth opportunities in a dynamic environment

*Generated automatically by HR Assistant*
"""


def save_job_description(content: str, role_title: str, output_dir: str = "output", session_id: str = None) -> str:
    """
    Save job description to a markdown file.
    
    Args:
        content: Job description content
        role_title: Title of the role for filename
        output_dir: Base directory to save the file
        session_id: Session ID for creating session-specific subdirectory
    
    Returns:
        Path to the saved file
    """
    import os
    
    # Create session-specific subdirectory if session_id provided
    if session_id:
        session_output_dir = os.path.join(output_dir, session_id)
    else:
        session_output_dir = output_dir
    
    # Ensure output directory exists
    os.makedirs(session_output_dir, exist_ok=True)
    
    # Clean role title for filename
    safe_title = "".join(c for c in role_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    filename = f"job_description_{safe_title}.md"
    filepath = os.path.join(session_output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Error saving job description: {e}")
        return ""


if __name__ == "__main__":
    # Test the tool
    test_role = {
        "title": "Senior Frontend Developer",
        "seniority_level": "senior",
        "department": "engineering",
        "specific_skills": ["React", "TypeScript", "Node.js"]
    }
    
    test_company = {
        "name": "TechStartup Inc",
        "size": "10-50",
        "stage": "Series A",
        "industry": "SaaS",
        "location": "San Francisco, CA",
        "remote_policy": "Hybrid",
        "budget_range": "$120k-150k + equity"
    }
    
    job_desc = generate_job_description(test_role, test_company)
    print("Generated Job Description:")
    print("=" * 50)
    print(job_desc)
