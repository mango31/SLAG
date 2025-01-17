import asyncio
from typing import List
from redis.asyncio import Redis
from src.worker.story_worker import StoryWorker
from src.worker.config import settings

class WorkerPool:
    def __init__(self, num_workers: int = 4):
        self.num_workers = num_workers
        self.workers: List[StoryWorker] = []
        
    def create_redis(self):
        """Create Redis connection for worker"""
        return Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        
    async def start(self):
        """Start multiple worker tasks"""
        worker_tasks = []
        for i in range(self.num_workers):
            worker = StoryWorker(
                redis_service=self.create_redis()
            )
            self.workers.append(worker)
            task = asyncio.create_task(worker.run())
            worker_tasks.append(task)
            
        # Wait for all workers
        await asyncio.gather(*worker_tasks) 