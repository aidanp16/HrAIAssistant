"""Salary recommendation generation tool for HR Assistant."""

import os
from typing import Dict, Any
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from config.prompts import SALARY_RECOMMENDATION_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="gpt-5-mini",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


@tool
def generate_salary_recommendation(role_info: Dict[str, Any], company_info: Dict[str, Any]) -> str:
    """Generate salary and compensation recommendations for a startup position."""
    
    prompt = SALARY_RECOMMENDATION_PROMPT.format(
        company_name=company_info.get("name", "Our Company"),
        company_size=company_info.get("size", "Early-stage startup"),
        company_stage=company_info.get("stage", "Growing startup"),
        location=company_info.get("location", "Remote-friendly"),
        industry=company_info.get("industry", "Technology"),
        role_title=role_info.get("title", ""),
        seniority_level=role_info.get("seniority_level", "Mid-level"),
        required_skills=", ".join(role_info.get("specific_skills", [])) if role_info.get("specific_skills") else "To be discussed",
        budget_range=company_info.get("budget_range", "Competitive")
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        print(f"Error generating salary recommendation: {e}")
        return f"""# Salary Recommendation: {role_info.get('title', 'Position')}

## Base Salary Range
**Recommended Range:** Market rate adjusted for startup context
- Entry Level: 15-20% below market rate + equity
- Mid Level: 10-15% below market rate + equity  
- Senior Level: 5-10% below market rate + equity

## Equity Package
**Recommended Equity:**
- Early stage (Pre-seed/Seed): 0.5-2.0%
- Growth stage (Series A+): 0.1-0.5%
- Vesting: 4-year vesting with 1-year cliff

## Total Compensation Strategy
**Benefits to Highlight:**
- Flexible working arrangements
- Professional development budget
- Health/wellness benefits
- Stock option upside potential

## Negotiation Guidelines
**Flexible Areas:**
- Start date flexibility
- Professional development budget
- Additional PTO
- Remote work arrangements

**Fixed Areas:**
- Base equity structure
- Core benefits package
- Performance review cycles

*Recommendations based on current market data and startup best practices*
"""


def save_salary_recommendation(content: str, role_title: str, output_dir: str = "output") -> str:
    """Save salary recommendation to a markdown file."""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    safe_title = "".join(c for c in role_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_').lower()
    
    filename = f"salary_recommendation_{safe_title}.md"
    filepath = os.path.join(output_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except Exception as e:
        print(f"Error saving salary recommendation: {e}")
        return ""
