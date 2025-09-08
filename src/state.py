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
    budget_range: Optional[str]  # e.g., "$120k-150k", "80k-100k"
    timeline: Optional[str]  # e.g., "6-8 weeks", "ASAP"
    generated_content: Optional[Dict[str, str]]  # Generated markdown files


class CompanyInfo(TypedDict):
    """Information about the company."""
    name: Optional[str]
    size: Optional[str]  # e.g., "1-10", "10-50", "50-200"
    stage: Optional[str]  # e.g., "pre-seed", "seed", "series-a"
    industry: Optional[str]
    location: Optional[str]
    remote_policy: Optional[str]  # e.g., "remote", "hybrid", "in-office"


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
    
    # Role-by-role processing tracking
    current_role_index: int  # Index of the role we're currently asking questions about
    role_completion_status: List[bool]  # Track which roles have sufficient info
    
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
    # Load stored company profile
    try:
        from .company_profile import get_company_info_dict
    except ImportError:
        from src.company_profile import get_company_info_dict
    stored_company_info = get_company_info_dict()
    
    return ConversationState(
        stage=WorkflowStage.INITIAL_ANALYSIS,
        session_id=session_id,
        original_request=original_request,
        current_questions=None,
        pending_user_response=False,
        job_roles=[],
        company_info=CompanyInfo(
            name=stored_company_info.get('name'),
            size=stored_company_info.get('size'),
            stage=stored_company_info.get('stage'),
            industry=stored_company_info.get('industry'),
            location=stored_company_info.get('location'),
            remote_policy=stored_company_info.get('remote_policy')
        ),
        current_role_index=0,
        role_completion_status=[],
        content_to_generate=[],
        generated_files={},
        messages=[],
        missing_info=[],
        ready_for_generation=False
    )


def is_information_sufficient(state: ConversationState) -> bool:
    """Check if we have enough information to generate content.
    Company info is assumed to be complete from the stored profile.
    """
    # Check if we have job roles with basic info
    has_roles = len(state["job_roles"]) > 0
    
    # Check if each role has sufficient information using the role-specific function
    roles_have_sufficient_info = True
    for role in state["job_roles"]:
        if not is_role_information_sufficient(role):
            roles_have_sufficient_info = False
            break
    
    return has_roles and roles_have_sufficient_info


def get_missing_information(state: ConversationState) -> List[str]:
    """Identify what role-specific information is still missing.
    Company info is assumed to be complete from the stored profile.
    """
    missing = []
    
    if not state["job_roles"]:
        missing.append("specific job roles and requirements")
    else:
        for role in state["job_roles"]:
            role_title = role['title']
            if not role.get("seniority_level"):
                missing.append(f"seniority level for {role_title}")
            if not role.get("specific_skills"):
                missing.append(f"required skills for {role_title}")
            if not role.get("budget_range"):
                missing.append(f"budget range for {role_title}")
            if not role.get("timeline"):
                missing.append(f"timeline for {role_title}")
    
    return missing


def is_role_information_sufficient(role: JobRole) -> bool:
    """Check if a single role has sufficient information for content generation."""
    has_budget = role.get("budget_range") is not None and str(role.get("budget_range", "")).strip()
    has_timeline = role.get("timeline") is not None and str(role.get("timeline", "")).strip()
    has_skills = role.get("specific_skills") is not None and len(role.get("specific_skills", [])) > 0
    
    # Require ALL 3 essential pieces of information for accurate, in-depth content generation
    # Budget range, timeline, and specific skills are all critical for quality hiring materials
    return has_budget and has_timeline and has_skills


def get_missing_information_for_role(role: JobRole) -> List[str]:
    """Identify what information is missing for a specific role."""
    missing = []
    role_title = role['title']
    
    if not role.get("budget_range"):
        missing.append(f"budget range for {role_title}")
    if not role.get("timeline"):
        missing.append(f"timeline for {role_title}")
    if not role.get("specific_skills"):
        missing.append(f"specific skills for {role_title}")
    
    return missing


def get_current_role(state: ConversationState) -> JobRole:
    """Get the role currently being processed."""
    current_index = state.get("current_role_index", 0)
    job_roles = state.get("job_roles", [])
    
    if current_index < len(job_roles):
        role = job_roles[current_index]
        return role
    
    return None


def are_all_roles_complete(state: ConversationState) -> bool:
    """Check if all roles have sufficient information."""
    completion_status = state.get("role_completion_status", [])
    return len(completion_status) == len(state["job_roles"]) and all(completion_status)
