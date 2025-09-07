"""Hiring checklist generation tool for HR Assistant."""

import os
from typing import Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from config.prompts import HIRING_CHECKLIST_PROMPT

load_dotenv()

# Initialize OpenAI client
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@tool
def generate_hiring_checklist(role_info: Dict[str, Any], company_info: Dict[str, Any]) -> str:
    """
    Generate a comprehensive hiring checklist for a startup position.
    
    Args:
        role_info: Dictionary containing job role information
        company_info: Dictionary containing company information
    
    Returns:
        Generated hiring checklist as markdown string
    """
    
    # Format the prompt with available information
    prompt = HIRING_CHECKLIST_PROMPT.format(
        company_name=company_info.get("name", "Our Company"),
        company_size=company_info.get("size", "Early-stage startup"),
        company_stage=company_info.get("stage", "Growing startup"),
        role_title=role_info.get("title", ""),
        seniority_level=role_info.get("seniority_level", "Mid-level"),
        timeline=company_info.get("timeline", "Standard timeline"),
        budget_range=company_info.get("budget_range", "Competitive")
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    except Exception as e:
        print(f"Error generating hiring checklist: {e}")
        # Return a basic fallback checklist
        return f"""# Hiring Checklist: {role_info.get('title', 'Position')}

## Pre-Hiring Preparation
- [ ] Define role requirements and must-have skills
- [ ] Set budget and equity allocation
- [ ] Prepare job description and posting
- [ ] Assign interview team members
- [ ] Create assessment criteria

## Sourcing and Outreach
- [ ] Post on relevant job boards
- [ ] Share on company social media
- [ ] Reach out to network contacts
- [ ] Consider recruiting agencies if needed
- [ ] Set up application tracking system

## Interview Process
- [ ] Screen initial applications
- [ ] Conduct phone/video screenings
- [ ] Schedule technical/skills assessments
- [ ] Conduct panel interviews
- [ ] Check cultural fit

## Decision and Offer
- [ ] Gather feedback from all interviewers
- [ ] Check references
- [ ] Make hiring decision
- [ ] Prepare compensation package
- [ ] Send offer letter

## Onboarding Preparation
- [ ] Prepare workspace and equipment
- [ ] Set up system access and accounts
- [ ] Plan first week schedule
- [ ] Assign onboarding buddy
- [ ] Prepare welcome materials

*Generated automatically by HR Assistant*
"""


def save_hiring_checklist(content: str, role_title: str, output_dir: str = "output") -> str:
    """
    Save hiring checklist to a markdown file.
    
    Args:
        content: Checklist content
        role_title: Title of the role for filename
        output_dir: Directory to save the file
    
    Returns:
        Path to the saved file
    """
    import os
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Clean role title for filename
    safe_title = "".join(c for c in role_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    filename = f"hiring_checklist_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Error saving hiring checklist: {e}")
        return ""


if __name__ == "__main__":
    # Test the tool
    test_role = {
        "title": "Senior Frontend Developer",
        "seniority_level": "senior",
        "department": "engineering"
    }
    
    test_company = {
        "name": "TechStartup Inc",
        "size": "10-50",
        "stage": "Series A",
        "timeline": "2-3 months",
        "budget_range": "$120k-150k + equity"
    }
    
    checklist = generate_hiring_checklist(test_role, test_company)
    print("Generated Hiring Checklist:")
    print("=" * 50)
    print(checklist)
