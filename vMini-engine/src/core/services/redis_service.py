from redis import Redis
from redis.asyncio import Redis as AsyncRedis
import logging
from datetime import datetime
import json
import time
import asyncio

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self, host: str, port: int):
        logger.info(f"Connecting to Redis at {host}:{port}")
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                # Sync client for regular operations
                self.redis = Redis(
                    host=host,
                    port=port,
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    socket_connect_timeout=10
                )
                # Async client for pubsub
                self.async_redis = AsyncRedis(
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

    async def queue_request(self, request_id: str, prompt: str):
        """Queue a new story generation request"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._queue_request, request_id, prompt)

    def _queue_request(self, request_id: str, prompt: str):
        """Synchronous implementation of queue_request"""
        self.redis.hset(f"request:{request_id}", mapping={
            "status": "pending",
            "prompt": prompt,
            "created_at": datetime.now().isoformat()
        })
        self.redis.rpush("queue:pending", request_id)

    async def get_request_status(self, request_id: str):
        """Get the status of a request"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.redis.hgetall, f"request:{request_id}")

    async def update_request_status(self, request_id: str, status: str, error: str = None):
        """Update the status of a request"""
        update_data = {
            "status": status,
            "updated_at": datetime.now().isoformat()
        }
        if error:
            update_data["error"] = error
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            self.redis.hset,
            f"request:{request_id}",
            mapping=update_data
        )

    async def get_next_request(self) -> str:
        """Get next request from the pending queue"""
        try:
            loop = asyncio.get_event_loop()
            request_id = await loop.run_in_executor(None, self.redis.lpop, "queue:pending")
            return request_id if request_id else None
        except Exception as e:
            logger.error(f"Error getting next request: {str(e)}")
            return None

    async def store_story_result(self, request_id: str, story: dict):
        """Store the generated story result"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.redis.hset,
            f"request:{request_id}",
            mapping={
                "result": json.dumps(story),
                "completed_at": datetime.now().isoformat()
            }
        ) 

    async def get_pubsub(self):
        """Get async pubsub client"""
        return self.async_redis.pubsub()

    async def publish_progress(self, request_id: str, message: str):
        """Publish progress update for a request"""
        try:
            await self.async_redis.publish(f"progress:{request_id}", message)
            logger.debug(f"Published progress for {request_id}: {message}")
        except Exception as e:
            logger.error(f"Error publishing progress: {str(e)}")
            # Don't raise - progress updates are non-critical
            pass 