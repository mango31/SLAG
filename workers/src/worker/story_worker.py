import asyncio
import logging
import json
from datetime import datetime
from redis.asyncio import Redis
from src.core.services.story_orchestration_service import StoryOrchestrationService
from src.core.services.llm_service import LLMService
from src.core.services.world_generation_service import WorldGenerationService
from src.core.services.framework_generation_service import FrameworkGenerationService
from src.core.services.story_generation_service import StoryGenerationService
from src.core.services.validation_service import ValidationService

logger = logging.getLogger(__name__)

class StoryWorker:
    def __init__(self, redis_service: Redis):
        self.redis = redis_service
        # Initialize services
        self.llm = LLMService()
        self.world_service = WorldGenerationService(self.llm)
        self.framework_service = FrameworkGenerationService(self.llm)
        self.story_service = StoryGenerationService(self.llm)
        self.validation_service = ValidationService(self.llm)
        self.orchestrator = StoryOrchestrationService(
            world_service=self.world_service,
            framework_service=self.framework_service,
            story_service=self.story_service,
            validation_service=self.validation_service
        )
        self.running = False
        
    def serialize_story(self, story_data: dict) -> dict:
        """Serialize story data, converting datetime objects to ISO format"""
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.loads(json.dumps(story_data, default=datetime_handler))

    async def process_request(self, request_id: str) -> None:
        """Process a single story generation request"""
        try:
            # Get request details from Redis
            request_data = await self.redis.hgetall(f"request:{request_id}")
            if not request_data:
                logger.error(f"No data found for request {request_id}")
                return

            # Update status to processing
            await self.redis.hset(f"request:{request_id}", "status", "processing")
            
            # Generate story using the orchestrator
            story = await self.orchestrator.generate_complete_story(request_data["prompt"])
            
            # Serialize story data before storing
            serialized_story = self.serialize_story(story)
            
            # Store result
            await self.redis.hset(
                f"request:{request_id}",
                mapping={
                    "result": json.dumps(serialized_story),
                    "status": "completed",
                    "completed_at": datetime.now().isoformat()
                }
            )
            logger.info(f"Completed story generation for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}")
            await self.redis.hset(
                f"request:{request_id}",
                mapping={
                    "status": "failed",
                    "error": str(e)
                }
            )

    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info("Story worker starting...")
        
        while self.running:
            try:
                # Get next request from queue
                request_id = await self.redis.lpop("queue:pending")
                
                if request_id:
                    logger.info(f"Processing request {request_id}")
                    await self.process_request(request_id)
                else:
                    # No requests, wait before checking again
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(5) 