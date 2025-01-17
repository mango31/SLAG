import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import logging
from src.core.utils.logging_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from src.config.config import settings
from src.core.services import (
    LLMService,
    RedisService,
    WorldGenerationService,
    FrameworkGenerationService,
    StoryGenerationService,
    ValidationService,
    StoryOrchestrationService
)
import os
from src.core.services.redis_service import RedisService
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio
from fastapi.responses import JSONResponse
from src.core.services.story_orchestration_service import StoryOrchestrationService
from src.core.services.world_generation_service import WorldGenerationService
from src.core.services.framework_generation_service import FrameworkGenerationService
from src.core.services.story_generation_service import StoryGenerationService
from src.core.services.validation_service import ValidationService
from src.core.services.llm_service import LLMService

logger = setup_logging("api", "api.log")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For testing only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StoryRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_story(request: StoryRequest):
    request_id = await story_orchestration_service.queue_story_request(request.prompt)
    return {"request_id": request_id, "status": "queued"}

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    return await story_orchestration_service.get_request_status(request_id)

@app.get("/status")
async def get_generation_status():
    try:
        status = story_orchestration_service.get_generation_status()
        return status
    except Exception as e:
        logger.error(f"Error getting generation status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize services
llm_service = LLMService()  # Initialize LLM service first
redis_client = RedisService(host=REDIS_HOST, port=REDIS_PORT)

# Initialize story orchestration service with all dependencies
story_orchestration_service = StoryOrchestrationService(
    world_service=WorldGenerationService(llm_service),
    framework_service=FrameworkGenerationService(llm_service),
    story_service=StoryGenerationService(llm_service),
    validation_service=ValidationService(llm_service),
    redis_service=redis_client
)

# Simple in-memory cache for health check
_last_health_check = None
_health_check_cache_ttl = 5  # seconds

@app.get("/health")
async def health_check():
    global _last_health_check
    current_time = time.time()
    
    # Return cached result if available and not expired
    if _last_health_check and current_time - _last_health_check['timestamp'] < _health_check_cache_ttl:
        return _last_health_check['result']
    
    try:
        # Test Redis connection
        redis_client.redis.ping()
        result = {
            "status": "healthy",
            "redis": {
                "status": "healthy",
                "host": REDIS_HOST,
                "port": REDIS_PORT
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        result = {
            "status": "degraded",
            "redis": {
                "status": "error",
                "message": str(e),
                "host": REDIS_HOST,
                "port": REDIS_PORT
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Update cache
    _last_health_check = {
        'timestamp': current_time,
        'result': result
    }
    
    return result

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Client host: {request.client.host if request.client else 'Unknown'}")
    response = await call_next(request)
    return response 

class TimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=900)
        except asyncio.TimeoutError:
            return JSONResponse(
                status_code=504,
                content={"detail": "Request timeout"}
            )

app.add_middleware(TimeoutMiddleware) 