import os
from src.core.services import RedisService
# ... other imports ...

# Get Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize services once
redis_client = RedisService(host=REDIS_HOST, port=REDIS_PORT)

# Pass to story worker
story_worker = StoryWorker(redis_client)
# ... other service initializations ... 