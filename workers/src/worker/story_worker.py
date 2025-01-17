import asyncio
import logging
import json
from datetime import datetime
from redis.asyncio import Redis
from src.core.services import (
    LLMService,
    RedisService,
    WorldGenerationService,
    FrameworkGenerationService,
    StoryGenerationService,
    ValidationService
)
from src.core.services.story_orchestration_service import StoryOrchestrationService
import os

logger = logging.getLogger(__name__)

class StoryWorker:
    def __init__(self, redis_client: RedisService):
        self.redis_client = redis_client
        self.llm_service = LLMService()
        
        # Initialize generation services
        try:
            self.world_service = WorldGenerationService(self.llm_service)
            self.framework_service = FrameworkGenerationService(self.llm_service)
            self.story_service = StoryGenerationService(self.llm_service)
            self.validation_service = ValidationService(self.llm_service)
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            raise

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
            # Get request data
            request_data = await self.redis_client.get_request_data(request_id)
            
            # Update status to processing
            await self.redis_client.update_request_status(request_id, "processing")
            
            # Publish progress update
            await self.redis_client.publish_progress(request_id, "Starting world generation...")
            
            try:
                # World Building
                await self.redis_client.publish_progress(request_id, "Creating story world and characters...")
                bible = await self.world_service.generate_complete_bible(request_data["prompt"])
                await self.redis_client.publish_progress(request_id, "World building complete!")
                
                # Framework Creation
                await self.redis_client.publish_progress(request_id, "Designing story framework...")
                framework = await self.framework_service.create_framework(bible)
                await self.redis_client.publish_progress(request_id, "Story framework complete!")
                
                # Story Generation
                await self.redis_client.publish_progress(request_id, "Beginning story writing...")
                story = await self.story_service.generate_story(
                    story_bible=bible.model_dump(),
                    framework=framework
                )
                
                # Convert story to dictionary for storage
                story_dict = story.to_dict()
                
                # Store result
                await self.redis_client.store_story_result(request_id, story_dict)
                await self.redis_client.update_request_status(request_id, "completed")
                
                # Send final progress message with completion flag
                await self.redis_client.publish_progress(
                    request_id, 
                    f"Story generation complete! Generated {story.word_count} words.",
                    is_complete=True
                )
                
                logger.info(f"Completed story generation for request {request_id}")
                
            except Exception as e:
                error_msg = f"Error during story generation: {str(e)}"
                logger.error(error_msg)
                # Send error message with completion flag
                await self.redis_client.publish_progress(
                    request_id, 
                    f"Error: {error_msg}",
                    is_complete=True
                )
                await self.redis_client.update_request_status(request_id, "failed", error=str(e))
                raise
                
        except Exception as e:
            logger.error(f"Error processing request {request_id}: {str(e)}")
            await self.redis_client.update_request_status(request_id, "failed", error=str(e))
            # Send error message with completion flag
            await self.redis_client.publish_progress(
                request_id, 
                f"Failed: {str(e)}",
                is_complete=True
            )

    async def run(self):
        """Main worker loop"""
        self.running = True
        logger.info("Story worker starting...")
        
        while self.running:
            try:
                # Verify Redis connection is alive
                await self.redis_client.ping()
                
                # Get next request from queue
                request_id = await self.redis_client.get_next_request()
                
                if request_id:
                    logger.info(f"Processing request {request_id}")
                    try:
                        await self.process_request(request_id)
                    except Exception as e:
                        logger.error(f"Error processing request {request_id}: {str(e)}")
                        # Update request status to failed
                        await self.redis_client.update_request_status(
                            request_id=request_id,
                            status="failed",
                            error=str(e)
                        )
                else:
                    # No requests, wait before checking again
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                # Add small delay before retry
                await asyncio.sleep(5)
                
                # Try to reconnect to Redis if that's the issue
                try:
                    await self.redis_client.ping()
                except:
                    logger.error("Lost Redis connection, attempting to reconnect...")
                    # Let the worker pool handle reconnection
                    self.running = False
                    break 