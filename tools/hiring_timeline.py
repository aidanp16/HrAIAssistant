"""Hiring timeline generation tool for HR Assistant."""

import os
from typing import Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from config.prompts import HIRING_TIMELINE_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@tool
def generate_hiring_timeline(role_info: Dict[str, Any], company_info: Dict[str, Any]) -> str:
    """Generate a realistic hiring timeline for a startup position."""
    
    prompt = HIRING_TIMELINE_PROMPT.format(
        company_name=company_info.get("name", "Our Company"),
        company_size=company_info.get("size", "Early-stage startup"),
        company_stage=company_info.get("stage", "Growing startup"),
        role_title=role_info.get("title", ""),
        seniority_level=role_info.get("seniority_level", "Mid-level"),
        timeline=company_info.get("timeline", "Standard timeline"),
        industry=company_info.get("industry", "Technology")
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        print(f"Error generating hiring timeline: {e}")
        return f"""# Hiring Timeline: {role_info.get('title', 'Position')}

## Week 1-2: Preparation Phase
- Finalize job description and requirements
- Set up job postings on relevant platforms
- Brief interview team on role expectations
- Prepare assessment materials

## Week 3-4: Active Sourcing
- Applications start coming in
- Begin initial screening process
- Reach out to potential candidates
- Review and shortlist candidates

## Week 5-6: Interview Process
- Conduct first-round interviews
- Technical/skills assessments
- Second-round interviews with team
- Cultural fit evaluations

## Week 7-8: Decision and Offer
- Final interviews with leadership
- Reference checks
- Make hiring decision
- Prepare and send offer

## Week 9: Onboarding Preparation
- Negotiate terms if needed
- Prepare for new hire arrival
- Set up workspace and systems
- Plan first week activities

*Timeline may vary based on candidate availability and market conditions*
"""


def save_hiring_timeline(content: str, role_title: str, output_dir: str = "output") -> str:
    """Save hiring timeline to a markdown file."""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    safe_title = "".join(c for c in role_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    filename = f"hiring_timeline_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Error saving hiring timeline: {e}")
        return ""
