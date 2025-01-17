import asyncio
from typing import List
import logging
from src.core.services import RedisService
from src.worker.story_worker import StoryWorker
from src.worker.config import settings

logger = logging.getLogger(__name__)

class WorkerPool:
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.redis_client = None
        self.workers: List[StoryWorker] = []
        
    async def initialize(self):
        """Initialize Redis connection with retries"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to Redis (attempt {attempt + 1}/{max_retries})")
                self.redis_client = RedisService(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT
                )
                # Test the connection
                await self.redis_client.ping()
                logger.info("Successfully connected to Redis")
                return
            except Exception as e:
                logger.error(f"Redis connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Redis after all retries")
                    raise
        
    async def start(self):
        """Start multiple worker tasks"""
        logger.info(f"Starting {self.num_workers} workers...")
        while True:  # Keep trying to start the worker pool
            try:
                # Initialize Redis first
                await self.initialize()
                
                # Start workers
                for i in range(self.num_workers):
                    try:
                        worker = StoryWorker(redis_client=self.redis_client)
                        self.workers.append(worker)
                        asyncio.create_task(worker.run())
                        logger.info(f"Started worker {i+1}/{self.num_workers}")
                    except Exception as e:
                        logger.error(f"Failed to start worker {i+1}: {str(e)}")
                        raise
                    
                # Keep the pool running and monitor workers
                while True:
                    await asyncio.sleep(60)
                    # Check if all workers are still running
                    active_workers = len([w for w in self.workers if w.running])
                    logger.info(f"Worker pool health check - {active_workers}/{self.num_workers} workers running")
                    
                    if active_workers < self.num_workers:
                        logger.warning("Some workers have stopped - restarting worker pool")
                        self.workers = []  # Clear existing workers
                        raise Exception("Worker pool needs restart")
                    
            except Exception as e:
                logger.error(f"Worker pool error: {str(e)}")
                # Clear existing workers
                self.workers = []
                # Wait before trying to restart
                await asyncio.sleep(10)
                logger.info("Attempting to restart worker pool...") 