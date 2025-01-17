from typing import Dict, List
import json
from src.core.models.story_bible import StoryBible
from src.core.services.llm_service import LLMService
from src.worker.config import settings
import logging

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service

    async def check_cohesiveness(self, bible: StoryBible) -> Dict[str, List[str]]:
        """Check story bible for inconsistencies and potential issues"""
        issues = {
            "model_validation": [],
            "content_validation": [],
            "structural_validation": []
        }
        
        # Model validation
        try:
            for key, items in bible.model_dump().items():
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        if isinstance(item, dict):
                            if "name" not in item:
                                issues["model_validation"].append(
                                    f"Item {i} in {key} missing required 'name' field"
                                )
                            # Check for required fields based on type
                            if key == "technology":
                                for field in ["description", "limitations", "requirements", "risks"]:
                                    if field not in item:
                                        issues["model_validation"].append(
                                            f"Technology '{item.get('name', f'item {i}')}' missing {field}"
                                        )
                            elif key == "characters":
                                for field in ["role", "description"]:
                                    if field not in item:
                                        issues["model_validation"].append(
                                            f"Character '{item.get('name', f'item {i}')}' missing {field}"
                                        )
        except Exception as e:
            issues["model_validation"].append(f"Error during model validation: {str(e)}")

        # Content validation via LLM
        try:
            system_prompt = """You are a story consistency expert. Analyze this story bible for:
            1. Timeline inconsistencies
            2. Character motivation conflicts
            3. World-building contradictions
            4. Logic gaps in technology or systems
            5. Faction relationship inconsistencies

            Return a JSON response with ONLY the issues found, or an empty list if none found."""

            response = await self.llm.generate(
                f"{system_prompt}\n\nStory Bible:\n{bible.model_dump_json()}",
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            try:
                llm_issues = json.loads(response)
                if isinstance(llm_issues, dict) and "issues" in llm_issues:
                    issues["content_validation"].extend(llm_issues["issues"])
            except json.JSONDecodeError:
                issues["content_validation"].append("Failed to parse LLM validation response")
                
        except Exception as e:
            issues["content_validation"].append(f"Error during content validation: {str(e)}")

        return issues

    async def fix_inconsistencies(self, bible: StoryBible, issues: Dict) -> StoryBible:
        """Apply fixes to identified issues"""
        if not any(issues.values()):  # If no issues found
            return bible
        
        try:
            system_prompt = """You are a story consistency expert. Fix the identified issues in this story bible.
            Return ONLY the necessary changes as a JSON object with the same structure as the original bible.
            Focus on fixing the specific issues listed while maintaining the core narrative."""

            prompt = f"""Story Bible:\n{bible.model_dump_json()}\n\nIssues to Fix:\n{json.dumps(issues, indent=2)}
            
            Requirements:
            1. Return valid JSON
            2. Include 'name' field for all list items
            3. Maintain required fields for each type (technology, character, etc.)
            4. Only return the changes needed to fix the issues"""

            response = await self.llm.generate(prompt, temperature=0.3)
            
            try:
                fixes = json.loads(response)
                # Apply fixes through the add_expansion method
                bible.add_expansion(fixes)
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM fixes response")
                
        except Exception as e:
            logger.error(f"Error fixing inconsistencies: {str(e)}")
        
        return bible 