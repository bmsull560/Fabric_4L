"""Prompt template loader for entity and relationship extraction.

Loads prompt templates from files and renders them with variable substitution.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List


class PromptTemplate:
    """Template loader for extraction prompts.
    
    Loads prompts from text files and supports variable substitution
    using Python str.format() syntax.
    
    Example:
        template = PromptTemplate("capability_extraction")
        prompt = template.render(text="some text", confidence_threshold=0.8)
    """
    
    # Default prompts directory
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    
    def __init__(self, name: str, prompts_dir: Path = None):
        """Initialize prompt template.
        
        Args:
            name: Prompt file name (without .txt extension)
            prompts_dir: Custom prompts directory (default: prompts/)
        """
        self.name = name
        self.prompts_dir = prompts_dir or self.PROMPTS_DIR
        self._template = self._load_template()
    
    def _load_template(self) -> str:
        """Load template from file."""
        template_path = self.prompts_dir / f"{self.name}.txt"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def render(self, **kwargs) -> str:
        """Render template with variable substitution.
        
        Args:
            **kwargs: Template variables
            
        Returns:
            Rendered prompt string
        """
        try:
            return self._template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing template variable {e} for prompt '{self.name}'")
    
    @property
    def raw_template(self) -> str:
        """Get raw template string."""
        return self._template


class PromptRegistry:
    """Registry of all available prompt templates."""
    
    ENTITY_PROMPTS = [
        "capability_extraction",
        "usecase_extraction",
        "persona_extraction",
        "valuedriver_extraction",
        "feature_extraction",
    ]
    
    RELATIONSHIP_PROMPTS = [
        "relationship_extraction",
    ]
    
    @classmethod
    def get_entity_prompt(cls, entity_type: str) -> PromptTemplate:
        """Get prompt template for entity type.
        
        Args:
            entity_type: Entity type name (capability, usecase, persona, etc.)
            
        Returns:
            PromptTemplate instance
        """
        prompt_name = f"{entity_type.lower().replace('_', '')}_extraction"
        if prompt_name not in cls.ENTITY_PROMPTS:
            raise ValueError(f"Unknown entity type: {entity_type}")
        return PromptTemplate(prompt_name)
    
    @classmethod
    def get_relationship_prompt(cls) -> PromptTemplate:
        """Get relationship extraction prompt."""
        return PromptTemplate("relationship_extraction")
    
    @classmethod
    def list_all_prompts(cls) -> Dict[str, List[str]]:
        """List all available prompts."""
        return {
            "entity_extraction": cls.ENTITY_PROMPTS,
            "relationship_extraction": cls.RELATIONSHIP_PROMPTS,
        }


def render_entity_prompt(
    entity_type: str,
    text: str,
    confidence_threshold: float = 0.8,
    **extra_vars
) -> str:
    """Convenience function to render entity extraction prompt.
    
    Args:
        entity_type: Type of entity (capability, usecase, persona, valuedriver, feature)
        text: Source text to extract from
        confidence_threshold: Minimum confidence threshold
        **extra_vars: Additional template variables
        
    Returns:
        Rendered prompt string
    """
    template = PromptRegistry.get_entity_prompt(entity_type)
    return template.render(
        text=text,
        confidence_threshold=confidence_threshold,
        **extra_vars
    )


def render_relationship_prompt(
    text: str,
    entities: Dict[str, List[Any]],
    **extra_vars
) -> str:
    """Convenience function to render relationship extraction prompt.
    
    Args:
        text: Source text
        entities: Dictionary of entity lists by type
        **extra_vars: Additional template variables
        
    Returns:
        Rendered prompt string
    """
    template = PromptRegistry.get_relationship_prompt()
    
    # Build entity index
    entity_list = []
    for entity_type, entity_items in entities.items():
        for entity in entity_items:
            entity_list.append({
                "id": entity.id,
                "type": entity_type,
                "name": getattr(entity, "name", getattr(entity, "title", "Unknown"))
            })
    
    return template.render(
        text=text,
        entities_json=json.dumps(entity_list, indent=2),
        **extra_vars
    )
