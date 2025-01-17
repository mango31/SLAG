from typing import Dict, Any
import json
import os
from datetime import datetime
from pydantic import ValidationError
from src.core.models.story_bible import StoryBible, TimelineEvent
from src.core.services.llm_service import LLMService
from src.core.services.embedding_service import EmbeddingService
from src.core.services.s3_service import S3Service
import logging
from pathlib import Path
from src.core.utils.logging_config import setup_logging
from src.worker.config import settings
from src.core.services.vector_store_service import VectorStoreService

# Replace existing logging setup with:
logger = setup_logging("world_generation", "world_generation.log")

class WorldGenerationService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.embedding_service = EmbeddingService()
        self.current_bible: StoryBible = None
        self.vector_store = VectorStoreService()
        self.s3 = S3Service()
        logger.info("WorldGenerationService initialized")

    async def initialize_bible(self, prompt: str) -> StoryBible:
        """Create initial story bible framework from user prompt"""
        system_prompt = """You are a world-building expert. Given the user's story prompt, 
        create an initial story bible framework. Focus on the core elements: setting, main characters, 
        key locations, and major factions. Return the response in valid JSON format matching this structure:
        {
            "title": "",
            "genre": "",
            "universe": {"setting": "", "era": ""},
            "characters": [{"name": "", "role": "", "description": ""}],
            "locations": [{"name": "", "description": ""}],
            "factions": [{"name": "", "description": "", "goals": [], "relationships": {}}],
            "technology": [{"name": "", "description": ""}],
            "timeline": {
                "pre_2145_mars_exploration": [
                    {"year": "2028", "event": "First Mars landing", "details": "..."}
                ]
            },
            "themes": [],
            "notes": []
        }
        
        Ensure all timeline entries follow the format of year, event, and optional details."""

        full_prompt = f"{system_prompt}\n\nUser Story Prompt: {prompt}"
        try:
            logger.info(f"Initializing bible from prompt: {prompt[:100]}...")
            response = await self.llm.generate(
                full_prompt,
                temperature=settings.WORLD_BUILDING_TEMPERATURE,
                max_tokens=settings.WORLD_BUILDING_MAX_TOKENS
            )
            
            logger.debug(f"Raw LLM response: {response[:200]}...")
            
            bible_dict = json.loads(response)
            
            # Convert timeline events using the model's helper method
            bible_dict = StoryBible.convert_timeline_events(bible_dict)
            
            self.current_bible = StoryBible(**bible_dict)
            
            logger.info("Successfully created initial bible")
            await self.save_bible(self.current_bible, "initial")
            return self.current_bible
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.debug(f"Invalid JSON response: {response}")
            raise
        except ValidationError as e:
            logger.error(f"Bible validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in initialize_bible: {str(e)}")
            raise

    async def identify_expansion_areas(self) -> list[str]:
        """Identify areas in the story bible that need expansion"""
        if not self.current_bible:
            raise ValueError("No story bible initialized")

        system_prompt = """Analyze the current story bible and identify 3-5 specific areas that need 
        expansion or more detail. Focus on elements that would make the world more cohesive and interesting. 
        Return a list of specific aspects to expand, one per line."""

        bible_json = self.current_bible.model_dump_json()
        full_prompt = f"{system_prompt}\n\nCurrent Story Bible:\n{bible_json}"
        
        response = await self.llm.generate(
            full_prompt,
            temperature=settings.WORLD_BUILDING_TEMPERATURE,
            max_tokens=settings.WORLD_BUILDING_MAX_TOKENS
        )
        return [area.strip() for area in response.split('\n') if area.strip()]

    async def expand_bible(self, bible: StoryBible, area: str) -> StoryBible:
        """Expand story bible with content merging"""
        try:
            logger.info(f"Expanding area: {area}")
            
            # Get similar past bibles using embeddings
            query_embedding = await self.embedding_service.get_embedding(area)
            similar_bibles = await self.vector_store.find_similar(query_embedding)
            examples = "\n".join([b.model_dump_json() for b in similar_bibles]) if similar_bibles else ""
            
            # Separate the example to avoid nested f-strings
            example_tech = '''{
                "technology": [{
                    "name": "Key Technology Name",
                    "description": "What it does and its significance",
                    "limitations": ["Known limitations"],
                    "requirements": {"key": "value"},
                    "risks": ["Potential risks"]
                }]
            }'''
            
            example_locations = '''{
                "locations": [{
                    "name": "Location Name",
                    "type": "Location Type",
                    "description": "Physical description",
                    "significance": "Key story importance",
                    "features": ["Notable feature 1", "Notable feature 2"]
                }]
            }'''
            
            example_social = '''{
                "social_structures": [{
                    "name": "Structure Name",
                    "type": "Structure Type",
                    "description": "How it works",
                    "significance": "Impact on story",
                    "members": ["Group 1", "Group 2"]
                }]
            }'''
            
            system_prompt = f"""You are a world-building expert. Given this story bible and area for expansion,
            provide additional details and content. You are expanding the '{self._determine_expansion_type(area)}' aspect.
            
            CRITICAL REQUIREMENTS:
            1. Return ONLY valid JSON - no explanatory text before or after
            2. Every object in a list MUST have a 'name' field
            3. Social structures should be added as factions or notes
            4. Follow these exact formats for new entries:
            
            Technology:
            {example_tech}
            
            Character:
            {{
                "characters": [{{
                    "name": "Character Name",
                    "role": "Primary Role",
                    "description": "Key characteristics",
                    "background": "Relevant history",
                    "traits": ["trait1", "trait2"]
                }}]
            }}
            
            Location:
            {{
                "locations": [{{
                    "name": "Location Name",
                    "description": "What makes it significant",
                    "features": ["Notable features"],
                    "significance": ["Story relevance"]
                }}]
            }}
            
            Timeline Events:
            {{
                "timeline": {{
                    "key_period": [
                        {{
                            "year": "YYYY",
                            "event": "Significant event",
                            "impact": "How it affects the story"
                        }}
                    ]
                }}
            }}
            
            Be creative and expansive - if you see opportunities to add relevant details beyond the basic format, do so."""

            bible_json = bible.model_dump_json()
            full_prompt = f"{system_prompt}\n\nCurrent Story Bible:\n{bible_json}\n\nExpand this area:\n{area}"
            if examples:
                full_prompt += f"\n\nSimilar examples for reference:\n{examples}"
            
            response = await self.llm.generate(
                full_prompt,
                temperature=settings.WORLD_BUILDING_TEMPERATURE,
                max_tokens=settings.WORLD_BUILDING_MAX_TOKENS
            )
            
            try:
                # Clean up response to ensure it's valid JSON
                response = response.strip()
                if not response.startswith('{'):
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    if start >= 0 and end > start:
                        response = response[start:end]
                    else:
                        logger.error(f"Could not find valid JSON in response: {response[:200]}...")
                        return bible
                        
                expansion_dict = json.loads(response)
                
                # Convert any timeline events in the expansion
                expansion_dict = StoryBible.convert_timeline_events(expansion_dict)
                
                # Validate expansion data more flexibly
                for key, value in expansion_dict.items():
                    if isinstance(value, list):
                        validated_items = []
                        for item in value:
                            if isinstance(item, dict):
                                # Accept items with any identifying field
                                if not any(id_field in item for id_field in ["name", "year", "title", "id"]):
                                    logger.warning(f"Item in {key} lacks identifier: {item}")
                                validated_items.append(item)
                        expansion_dict[key] = validated_items
                
                # Only proceed if we have valid items
                if any(isinstance(v, (list, dict)) and v for v in expansion_dict.values()):
                    bible.add_expansion(expansion_dict)
                    logger.info(f"Successfully merged expansion for area: {area}")
                else:
                    logger.warning(f"No valid items found in expansion response for {area}")
                
                return bible
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response[:200]}...")
                logger.debug(f"Full invalid response: {response}")
                return bible
                
        except Exception as e:
            logger.error(f"Error in expand_bible: {str(e)}")
            logger.error(f"Failed to expand area: {area}")
            return bible  # Return original bible instead of raising

    async def enrich_story_elements(self, bible: StoryBible) -> StoryBible:
        """Add story-development focused details to the story bible to support future plot creation"""
        system_prompt = """You are a story structure expert. Analyze this story bible and enhance it with details 
        that will support compelling story development. Focus on elements that will help craft a strong plot structure:

        1. Conflict Sources
           - Power dynamics between factions
           - Resource limitations and their implications
           - Ideological differences between characters/groups
           - Personal stakes for key characters

        2. Story Drivers
           - Key historical events that influence present tensions
           - Ticking clock elements or deadlines
           - Competing goals and motivations
           - Hidden connections between elements

        3. Plot Potential
           - Possible crisis points
           - Character pressure points
           - Faction friction points
           - Technology/artifact implications
           - Environmental constraints or threats

        4. Story Limitations
           - Physical boundaries of the world
           - Technological limitations
           - Social/political constraints
           - Timeline boundaries

        Return ONLY a valid JSON object containing your additions/modifications to enrich the story bible.
        Do not return the entire bible - only return the new/changed elements you want to add or modify."""

        bible_json = bible.model_dump_json()
        full_prompt = f"{system_prompt}\n\nCurrent Story Bible:\n{bible_json}"
        
        try:
            response = await self.llm.generate(
                full_prompt,
                temperature=settings.WORLD_BUILDING_TEMPERATURE,
                max_tokens=settings.WORLD_BUILDING_MAX_TOKENS
            )
            # Add error handling for JSON parsing
            try:
                enrichment_dict = json.loads(response)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in enrichment response. Response starts with: {response[:200]}...")
                logger.debug(f"Full invalid response: {response}")
                # Try to extract JSON if response contains it
                try:
                    # Look for JSON-like structure between curly braces
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        enrichment_dict = json.loads(json_match.group())
                    else:
                        return bible
                except:
                    return bible
            
            # Use the add_expansion method to merge enrichments
            bible.add_expansion(enrichment_dict)
            await self.save_bible(bible, "story_elements_enriched")
            return bible
            
        except Exception as e:
            logger.error(f"Error enriching story elements: {str(e)}")
            return bible  # Return unchanged bible if enrichment fails 

    async def generate_complete_bible(self, prompt: str) -> StoryBible:
        """Generate complete story bible including all expansions"""
        try:
            # 1. Initialize base bible
            self.current_bible = await self.initialize_bible(prompt)
            
            # 2. Identify areas for expansion
            expansion_areas = await self.identify_expansion_areas()
            
            # 3. Expand each area and update current bible
            for area in expansion_areas:
                try:
                    expanded_bible = await self.expand_bible(self.current_bible, area)
                    self.current_bible = expanded_bible
                except Exception as e:
                    logger.error(f"Error expanding area '{area}': {str(e)}")
                    continue
            
            # 4. Final enrichment pass
            try:
                enriched_bible = await self.enrich_story_elements(self.current_bible)
                self.current_bible = enriched_bible
            except Exception as e:
                logger.error(f"Error in final enrichment: {str(e)}")
            
            # 5. Save final comprehensive bible to S3
            bible_url = await self.save_bible(self.current_bible)
            logger.info(f"Saved final bible to: {bible_url}")
            
            return self.current_bible
            
        except Exception as e:
            logger.error(f"Error generating complete bible: {str(e)}")
            raise 

    def _determine_expansion_type(self, area: str) -> str:
        """Map expansion area to specific bible section"""
        if any(term in area for term in ['infrastructure', 'system', 'technology', 'technical']):
            return 'technology and infrastructure'
        elif any(term in area for term in ['social', 'culture', 'society']):
            return 'social and cultural'
        elif any(term in area for term in ['character', 'relationship']):
            return 'characters and relationships'
        elif any(term in area for term in ['location', 'settlement', 'base']):
            return 'locations and environment'
        elif any(term in area for term in ['faction', 'group', 'organization']):
            return 'factions and politics'
        else:
            return 'general world-building' 

    async def save_bible(self, bible: StoryBible, suffix: str = "") -> str:
        """Save bible to file with timestamp"""
        try:
            content = bible.model_dump_json(indent=2)
            bible_id = bible.title.lower().replace(' ', '_')
            return await self.s3.save_story(content, bible_id, 'bible')
        except Exception as e:
            logger.error(f"Error saving bible: {str(e)}")
            raise 