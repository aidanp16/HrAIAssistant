"""Session management and persistence for HR Assistant."""

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .state import ConversationState


class SessionManager:
    """Manages session persistence for HR Assistant conversations."""
    
    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)
    
    def create_session(self) -> str:
        """Create a new session and return session ID."""
        session_id = str(uuid.uuid4())
        return session_id
    
    def save_session(self, session_id: str, state: ConversationState) -> bool:
        """
        Save conversation state to file.
        
        Args:
            session_id: Unique session identifier
            state: Current conversation state
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            # Convert state to JSON-serializable format
            serializable_state = self._make_serializable(state)
            serializable_state["last_updated"] = datetime.now().isoformat()
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_state, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[ConversationState]:
        """
        Load conversation state from file.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            ConversationState if found, None otherwise
        """
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if not os.path.exists(session_file):
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Remove metadata and convert back to ConversationState
            data.pop("last_updated", None)
            
            return self._make_conversation_state(data)
            
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session file.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
            
            if os.path.exists(session_file):
                os.remove(session_file)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions with metadata."""
        sessions = []
        
        try:
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json extension
                    session_file = os.path.join(self.sessions_dir, filename)
                    
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extract session metadata
                        session_info = {
                            "session_id": session_id,
                            "original_request": data.get("original_request", ""),
                            "stage": data.get("stage", ""),
                            "job_roles": [role.get("title", "Unknown") for role in data.get("job_roles", [])],
                            "last_updated": data.get("last_updated", ""),
                            "completed": data.get("stage") == "completed"
                        }
                        
                        sessions.append(session_info)
                        
                    except Exception as e:
                        print(f"Error reading session file {filename}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error listing sessions: {e}")
        
        # Sort by last updated (most recent first)
        sessions.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return sessions
    
    def cleanup_old_sessions(self, days_old: int = 7) -> int:
        """Delete sessions older than specified days."""
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        try:
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.json'):
                    session_file = os.path.join(self.sessions_dir, filename)
                    
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        last_updated_str = data.get("last_updated", "")
                        if last_updated_str:
                            last_updated = datetime.fromisoformat(last_updated_str)
                            
                            if last_updated < cutoff_date:
                                os.remove(session_file)
                                deleted_count += 1
                                
                    except Exception as e:
                        print(f"Error processing session file {filename}: {e}")
                        continue
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        return deleted_count
    
    def _make_serializable(self, state: ConversationState) -> Dict[str, Any]:
        """Convert ConversationState to JSON-serializable format."""
        return {
            "stage": state["stage"].value if hasattr(state["stage"], 'value') else str(state["stage"]),
            "session_id": state["session_id"],
            "original_request": state["original_request"],
            "current_questions": state.get("current_questions"),
            "pending_user_response": state.get("pending_user_response", False),
            "job_roles": [dict(role) for role in state["job_roles"]],
            "company_info": dict(state["company_info"]),
            "content_to_generate": state.get("content_to_generate", []),
            "generated_files": state.get("generated_files", {}),
            "messages": state.get("messages", []),
            "missing_info": state.get("missing_info", []),
            "ready_for_generation": state.get("ready_for_generation", False)
        }
    
    def _make_conversation_state(self, data: Dict[str, Any]) -> ConversationState:
        """Convert JSON data back to ConversationState."""
        from .state import WorkflowStage, JobRole, CompanyInfo
        
        # Convert stage back to enum
        stage_value = data.get("stage", "initial_analysis")
        if isinstance(stage_value, str):
            stage = WorkflowStage(stage_value)
        else:
            stage = stage_value
        
        return ConversationState(
            stage=stage,
            session_id=data.get("session_id", ""),
            original_request=data.get("original_request", ""),
            current_questions=data.get("current_questions"),
            pending_user_response=data.get("pending_user_response", False),
            job_roles=[JobRole(**role) for role in data.get("job_roles", [])],
            company_info=CompanyInfo(**data.get("company_info", {})),
            content_to_generate=data.get("content_to_generate", []),
            generated_files=data.get("generated_files", {}),
            messages=data.get("messages", []),
            missing_info=data.get("missing_info", []),
            ready_for_generation=data.get("ready_for_generation", False)
        )


# Global session manager instance
session_manager = SessionManager()
