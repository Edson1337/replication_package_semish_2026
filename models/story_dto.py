"""User Story DTO - contract for JIRA normalization, Qdrant storage, and agent context."""
from pydantic import BaseModel, Field
from typing import List, Optional


class UserStoryDTO(BaseModel):
    """Schema for user stories used across the entire pipeline.
    
    This DTO serves as the contract for:
    1. Normalization: raw JIRA data is converted to this schema
    2. Storage: payload format for Qdrant 'user_stories' collection
    3. Processing: context format for downstream agents (NFR, QA)
    """
    id: str = Field(..., description="Story identifier (e.g. US01, PROJ-123)")
    title: str = Field(..., description="Short title of the story")
    story: str = Field(..., description="Full user story in 'As a..., I want..., so that...' format")
    acceptance_criteria: List[str] = Field(default_factory=list, description="List of acceptance criteria")
    priority: str = Field(default="Medium", description="Priority level: High, Medium, Low")
    story_points: Optional[int] = Field(default=None, description="Estimated story points")
    persona: Optional[str] = Field(default=None, description="User persona (e.g. Admin, Trainee)")
    feature: Optional[str] = Field(default=None, description="Feature area or component")

    @classmethod
    def from_jira_issue(cls, issue: dict) -> "UserStoryDTO":
        """Create a UserStoryDTO from a raw JIRA issue dict.
        
        Maps JIRA fields to the DTO schema:
        - key -> id
        - fields.summary -> title
        - fields.description -> story
        - fields.priority.name -> priority
        - fields.story_points or customfield -> story_points
        - fields.labels or components -> feature
        """
        fields = issue.get("fields", issue)
        
        # Extract priority
        priority_obj = fields.get("priority")
        priority = priority_obj.get("name", "Medium") if isinstance(priority_obj, dict) else str(priority_obj or "Medium")
        
        # Extract acceptance criteria (from description or custom field)
        description = fields.get("description", "") or ""
        acceptance_criteria = cls._extract_acceptance_criteria(description)
        
        # Extract persona from story text
        story_text = description if description else fields.get("summary", "")
        persona = cls._extract_persona(story_text)
        
        # Extract feature from labels or components
        labels = fields.get("labels", [])
        components = fields.get("components", [])
        feature = None
        if labels:
            feature = labels[0] if isinstance(labels[0], str) else labels[0].get("name", "")
        elif components:
            feature = components[0] if isinstance(components[0], str) else components[0].get("name", "")
        
        # Story points (varies by JIRA config)
        story_points = fields.get("story_points") or fields.get("customfield_10016")
        
        return cls(
            id=issue.get("key", fields.get("id", "UNKNOWN")),
            title=fields.get("summary", "No title"),
            story=story_text,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            story_points=int(story_points) if story_points else None,
            persona=persona,
            feature=feature,
        )
    
    @staticmethod
    def _extract_acceptance_criteria(description: str) -> List[str]:
        """Extract acceptance criteria from JIRA description text."""
        criteria = []
        if not description:
            return criteria
        
        lines = description.split("\n")
        in_ac_section = False
        
        for line in lines:
            line_stripped = line.strip()
            lower = line_stripped.lower()
            
            if "acceptance criteria" in lower or "critério" in lower or "ac:" in lower:
                in_ac_section = True
                continue
            
            if in_ac_section:
                if line_stripped.startswith(("-", "*", "•")):
                    criteria.append(line_stripped.lstrip("-*• ").strip())
                elif line_stripped == "":
                    in_ac_section = False
        
        # Fallback: if no structured AC found, use the description itself
        if not criteria and description:
            criteria.append(description.strip())
        
        return criteria
    
    @staticmethod
    def _extract_persona(story_text: str) -> Optional[str]:
        """Extract persona from 'As a <persona>, I want...' pattern."""
        lower = story_text.lower()
        if "as a " in lower or "as an " in lower:
            import re
            match = re.search(r"[Aa]s (?:a|an)\s+(.+?),\s*[Ii] want", story_text)
            if match:
                return match.group(1).strip()
        return None
