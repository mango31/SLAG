from redis import Redis
import logging
from datetime import datetime
import json
import time
import asyncio
from functools import partial

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, host: str, port: int):
        logger.info(f"Connecting to Redis at {host}:{port}")
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                self.redis = Redis(
                    host=host,
                    port=port,
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    socket_connect_timeout=10
                )
                self.redis.ping()
                logger.info("Successfully connected to Redis")
                return
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis after {max_retries} attempts")
                    raise

    async def ping(self) -> bool:
        """Async ping method to test Redis connection"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.redis.ping)
            return result
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            raise

    async def get_next_request(self) -> str:
        """Get next request from the pending queue"""
        try:
            loop = asyncio.get_event_loop()
            request_id = await loop.run_in_executor(None, self.redis.lpop, "queue:pending")
            return request_id if request_id else None
        except Exception as e:
            logger.error(f"Error getting next request: {str(e)}")
            return None

    async def get_request_data(self, request_id: str) -> dict:
        """Get request data from Redis"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.redis.hgetall, f"request:{request_id}")

    async def update_request_status(self, request_id: str, status: str, error: str = None):
        """Update the status of a request"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
            if error:
                update_data["error"] = error
            
            # Create a partial function to handle the hset with mapping
            hset_func = partial(
                self.redis.hset,
                f"request:{request_id}"
            )
            
            # Execute hset for each field separately
            loop = asyncio.get_event_loop()
            for field, value in update_data.items():
                await loop.run_in_executor(None, hset_func, field, value)
                
            logger.debug(f"Updated status for request {request_id}: {status}")
            
        except Exception as e:
            logger.error(f"Error updating request status: {str(e)}")
            raise

    async def store_story_result(self, request_id: str, story: dict):
        """Store the generated story result"""
        try:
            # Create a partial function to handle the hset
            hset_func = partial(
                self.redis.hset,
                f"request:{request_id}"
            )
            
            # Ensure story is properly serialized
            story_json = json.dumps(story)
            
            # Execute hset for each field
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, hset_func, "result", story_json)
            await loop.run_in_executor(None, hset_func, "completed_at", datetime.now().isoformat())
            
            logger.debug(f"Stored story result for request {request_id}")
            
        except Exception as e:
            logger.error(f"Error storing story result: {str(e)}")
            raise

    async def publish_progress(self, request_id: str, message: str, is_complete: bool = False):
        """
        Publish progress update for a request
        
        Args:
            request_id: The request identifier
            message: The progress message to send
            is_complete: If True, adds completion marker to signal client to close connection
        """
        try:
            loop = asyncio.get_event_loop()
            
            if is_complete:
                # Send the completion message
                completion_msg = json.dumps({
                    "message": message,
                    "complete": True
                })
                await loop.run_in_executor(
                    None,
                    self.redis.publish,
                    f"progress:{request_id}",
                    completion_msg
                )
                
                # Send a complete event for frontend handling
                complete_event = (
                    "event: complete\n"
                    "data: complete\n\n"
                )
                
                await loop.run_in_executor(
                    None,
                    self.redis.publish,
                    f"progress:{request_id}",
                    complete_event
                )
                
                # Send disconnect event with retry: -1 to prevent reconnection
                disconnect_event = (
                    "event: http.disconnect\n"
                    "retry: -1\n"
                    "data: disconnect\n\n"
                )
                
                await loop.run_in_executor(
                    None,
                    self.redis.publish,
                    f"progress:{request_id}",
                    disconnect_event
                )
            else:
                # Normal progress message - send raw message without SSE formatting
                await loop.run_in_executor(
                    None,
                    self.redis.publish,
                    f"progress:{request_id}",
                    message
                )
                
            logger.debug(f"Published progress for {request_id}: {message}")
        except Exception as e:
            logger.error(f"Error publishing progress: {str(e)}")
            # Don't raise - progress updates are non-critical
            pass 
            pass 