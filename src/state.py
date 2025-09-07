"""State management for HR Assistant workflow."""

from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class WorkflowStage(Enum):
    """Workflow stages for the HR Assistant."""
    INITIAL_ANALYSIS = "initial_analysis"
    ASKING_QUESTIONS = "asking_questions"
    PROCESSING_RESPONSE = "processing_response"
    GENERATING_CONTENT = "generating_content"
    COMPLETED = "completed"


class JobRole(TypedDict):
    """Information about a specific job role."""
    title: str
    seniority_level: Optional[str]  # e.g., "senior", "junior", "founding"
    department: Optional[str]  # e.g., "engineering", "marketing"
    specific_skills: Optional[List[str]]
    generated_content: Optional[Dict[str, str]]  # Generated markdown files


class CompanyInfo(TypedDict):
    """Information about the company."""
    name: Optional[str]
    size: Optional[str]  # e.g., "1-10", "10-50", "50-200"
    stage: Optional[str]  # e.g., "pre-seed", "seed", "series-a"
    industry: Optional[str]
    location: Optional[str]
    remote_policy: Optional[str]  # e.g., "remote", "hybrid", "in-office"
    budget_range: Optional[str]
    timeline: Optional[str]  # e.g., "urgent", "1-2 months", "3+ months"


class ConversationState(TypedDict):
    """Main state for the HR Assistant conversation."""
    # Workflow management
    stage: WorkflowStage
    session_id: str
    
    # User input and conversation
    original_request: str
    current_questions: Optional[List[str]]
    pending_user_response: bool
    
    # Extracted information
    job_roles: List[JobRole]
    company_info: CompanyInfo
    
    # Content generation tracking
    content_to_generate: List[str]  # Types of content needed
    generated_files: Dict[str, str]  # filename -> file_path mapping
    
    # Conversation history
    messages: List[Dict[str, str]]  # role, content pairs
    
    # Metadata
    missing_info: List[str]  # What information we still need
    ready_for_generation: bool


def create_initial_state(original_request: str, session_id: str) -> ConversationState:
    """Create initial conversation state."""
    return ConversationState(
        stage=WorkflowStage.INITIAL_ANALYSIS,
        session_id=session_id,
        original_request=original_request,
        current_questions=None,
        pending_user_response=False,
        job_roles=[],
        company_info=CompanyInfo(
            name=None,
            size=None,
            stage=None,
            industry=None,
            location=None,
            remote_policy=None,
            budget_range=None,
            timeline=None
        ),
        content_to_generate=[],
        generated_files={},
        messages=[],
        missing_info=[],
        ready_for_generation=False
    )


def is_information_sufficient(state: ConversationState) -> bool:
    """Check if we have enough information to generate content."""
    company = state["company_info"]
    
    # Essential information we need
    required_fields = [
        company.get("size"),
        company.get("stage"),
        company.get("budget_range"),
        company.get("timeline")
    ]
    
    # Check if we have job roles with basic info
    has_roles = len(state["job_roles"]) > 0
    
    # Check if most required fields are filled
    filled_fields = sum(1 for field in required_fields if field is not None)
    has_sufficient_company_info = filled_fields >= 3  # At least 3 out of 4 key fields
    
    return has_roles and has_sufficient_company_info


def get_missing_information(state: ConversationState) -> List[str]:
    """Identify what information is still missing."""
    missing = []
    company = state["company_info"]
    
    if not company.get("size"):
        missing.append("company size")
    if not company.get("stage"):
        missing.append("company stage/funding")
    if not company.get("budget_range"):
        missing.append("budget range for hiring")
    if not company.get("timeline"):
        missing.append("hiring timeline")
    if not company.get("industry"):
        missing.append("industry/domain")
    
    if not state["job_roles"]:
        missing.append("specific job roles and requirements")
    else:
        for role in state["job_roles"]:
            if not role.get("seniority_level"):
                missing.append(f"seniority level for {role['title']}")
            if not role.get("specific_skills"):
                missing.append(f"required skills for {role['title']}")
    
    return missing
