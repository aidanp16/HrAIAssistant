"""Company profile management for HR Assistant.

This module handles persistent storage of company information that should
be reused across all sessions, avoiding repetitive company questions.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CompanyProfile:
    """Company profile data structure."""
    # Required fields
    name: Optional[str] = None
    size: Optional[str] = None  # e.g., "1-10", "10-50", "50-200"
    stage: Optional[str] = None  # e.g., "pre-seed", "seed", "series-a"
    industry: Optional[str] = None
    
    # Optional fields for enhanced personalization
    location: Optional[str] = None
    remote_policy: Optional[str] = None  # e.g., "remote", "hybrid", "in-office"
    description: Optional[str] = None  # What does the company do?
    values: Optional[str] = None  # Core company values
    mission: Optional[str] = None  # Company mission/vision statement
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CompanyProfileManager:
    """Manages persistent storage of company profile."""
    
    def __init__(self, profile_file: str = "company_profile.json"):
        self.profile_file = profile_file
    
    def exists(self) -> bool:
        """Check if a company profile file exists."""
        return os.path.exists(self.profile_file)
    
    def load(self) -> CompanyProfile:
        """Load company profile from file, or return empty profile if not found."""
        if not self.exists():
            return CompanyProfile()
        
        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict back to CompanyProfile
            return CompanyProfile(**data)
            
        except Exception as e:
            print(f"Error loading company profile: {e}")
            # Return empty profile if file is corrupted
            return CompanyProfile()
    
    def save(self, profile: CompanyProfile) -> bool:
        """Save company profile to file."""
        try:
            # Update timestamps
            now = datetime.now().isoformat()
            if not profile.created_at:
                profile.created_at = now
            profile.updated_at = now
            
            # Convert to dict and save
            data = asdict(profile)
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving company profile: {e}")
            return False
    
    def update(self, **kwargs) -> bool:
        """Update specific fields in the company profile."""
        profile = self.load()
        
        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        return self.save(profile)
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        profile = self.load()
        required_fields = ['name', 'size', 'stage', 'industry']
        
        return all(
            getattr(profile, field) and str(getattr(profile, field)).strip()
            for field in required_fields
        )
    
    def get_missing_required_fields(self) -> list[str]:
        """Get list of missing required fields."""
        profile = self.load()
        required_fields = ['name', 'size', 'stage', 'industry']
        
        missing = []
        for field in required_fields:
            value = getattr(profile, field)
            if not value or not str(value).strip():
                missing.append(field)
        
        return missing
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert current profile to dictionary for use in workflow."""
        profile = self.load()
        return {
            'name': profile.name,
            'size': profile.size,
            'stage': profile.stage,
            'industry': profile.industry,
            'location': profile.location,
            'remote_policy': profile.remote_policy,
            'description': profile.description,
            'values': profile.values,
            'mission': profile.mission
        }
    
    def reset(self) -> bool:
        """Reset/delete the company profile."""
        try:
            if self.exists():
                os.remove(self.profile_file)
            return True
        except Exception as e:
            print(f"Error resetting company profile: {e}")
            return False


# Global company profile manager instance
company_profile_manager = CompanyProfileManager()


# Convenience functions
def load_company_profile() -> CompanyProfile:
    """Load the company profile."""
    return company_profile_manager.load()


def save_company_profile(profile: CompanyProfile) -> bool:
    """Save the company profile."""
    return company_profile_manager.save(profile)


def is_company_profile_complete() -> bool:
    """Check if company profile has all required fields."""
    return company_profile_manager.is_complete()


def get_company_info_dict() -> Dict[str, Any]:
    """Get company profile as dict for workflow integration."""
    return company_profile_manager.to_dict()


def update_company_profile(**kwargs) -> bool:
    """Update specific company profile fields."""
    return company_profile_manager.update(**kwargs)
