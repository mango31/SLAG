import asyncio
import logging
from src.worker.worker_pool import WorkerPool
from src.worker.config import settings
from src.core.utils.logging_config import setup_logging

logger = setup_logging("worker", "worker.log")

async def main():
    try:
        # Initialize worker pool
        pool = WorkerPool(num_workers=settings.NUM_WORKERS)
        
        # Start workers
        logger.info(f"Starting {settings.NUM_WORKERS} workers...")
        await pool.start()
        
    except Exception as e:
        logger.error(f"Worker pool failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 