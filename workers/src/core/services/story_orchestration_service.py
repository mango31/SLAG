from typing import Optional, Dict, Any
import logging
from src.core.utils.logging_config import setup_logging
from src.core.models.story_bible import StoryBible
from src.core.models.story_framework import StoryFramework
from src.core.models.story import Story
from src.core.services.world_generation_service import WorldGenerationService
from src.core.services.framework_generation_service import FrameworkGenerationService
from src.core.services.story_generation_service import StoryGenerationService
from src.core.services.validation_service import ValidationService
import asyncio
from fastapi import HTTPException
from src.core.utils.request_utils import generate_request_id
from src.worker.config import settings

logger = setup_logging("orchestration", "orchestration.log")

class StoryOrchestrationService:
    def __init__(
        self,
        world_service: WorldGenerationService,
        framework_service: FrameworkGenerationService,
        story_service: StoryGenerationService,
        validation_service: ValidationService
    ):
        if not all([world_service, framework_service, story_service]):
            raise ValueError("All services must be provided")
            
        self.world_service = world_service
        self.framework_service = framework_service
        self.story_service = story_service
        self.validation = validation_service
        self.current_state: Dict[str, Any] = {}
        
    async def generate_complete_story(self, prompt: str) -> Dict[str, Any]:
        try:
            logger.info(f"Starting story generation for prompt: {prompt}")
            
            # Step 1: Generate Story Bible with retries
            for attempt in range(3):
                try:
                    bible = await self.world_service.generate_complete_bible(prompt)
                    self.current_state["bible"] = bible
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    logger.warning(f"Bible generation attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            # Step 2: Create Story Framework with retries
            for attempt in range(3):
                try:
                    framework = await self.framework_service.create_framework(bible)
                    self.current_state["framework"] = framework
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    logger.warning(f"Framework generation attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2 ** attempt)
            
            # Step 3: Generate Story with retries
            for attempt in range(3):
                try:
                    story = await self.story_service.generate_story(
                        story_bible=bible.model_dump(),
                        framework=framework
                    )
                    self.current_state["story"] = story
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    logger.warning(f"Story generation attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2 ** attempt)
            
            return {
                "bible": bible.model_dump(),
                "framework": framework.model_dump(),
                "story": story.model_dump(),
                "word_count": story.word_count
            }
            
        except Exception as e:
            logger.error(f"Error in story generation pipeline: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_generation_status(self) -> Dict[str, Any]:
        """Get current status of story generation process"""
        return {
            "has_bible": "bible" in self.current_state,
            "has_framework": "framework" in self.current_state,
            "has_story": "story" in self.current_state,
            "current_stage": self._determine_current_stage()
        }

    def _determine_current_stage(self) -> str:
        """Determine current stage of story generation"""
        if "story" in self.current_state:
            return "complete"
        if "framework" in self.current_state:
            return "generating_story"
        if "bible" in self.current_state:
            return "generating_framework"
        return "generating_bible" 

    async def queue_story_request(self, prompt: str) -> str:
        """
        Queue a new story generation request.
        Returns request ID for status tracking.
        """
        try:
            # Generate unique request ID
            request_id = generate_request_id()
            
            # Queue the request in Redis
            await self.redis_service.queue_request(request_id, prompt)
            
            logger.info(f"Queued story request {request_id}")
            return request_id
            
        except Exception as e:
            logger.error(f"Error queueing story request: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """
        Get status of a queued story request.
        """
        try:
            status = await self.redis_service.get_request_status(request_id)
            if not status:
                raise HTTPException(status_code=404, detail="Request not found")
            return status
            
        except Exception as e:
            logger.error(f"Error getting request status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 