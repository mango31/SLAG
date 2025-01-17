from typing import Dict, Any, Optional
import boto3
from botocore.config import Config
import json
from src.worker.config import settings
import asyncio
import random
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        config = Config(
            retries=dict(
                max_attempts=10,
                mode='adaptive'
            ),
            read_timeout=300,
            connect_timeout=10
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION,
            config=config
        )

        self.max_retries = 5
        self.base_delay = 2  # Start with 2 second delay
        self.max_delay = 30  # Maximum delay of 30 seconds

    async def _call_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff on throttling"""
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            
            except Exception as e:
                if "ThrottlingException" not in str(e):
                    raise  # Re-raise if not a throttling error
                
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries ({self.max_retries}) exceeded for LLM call")
                    raise

                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                
                logger.warning(
                    f"Throttling detected on attempt {attempt + 1}/{self.max_retries}. "
                    f"Retrying in {delay:.2f}s"
                )
                
                await asyncio.sleep(delay)

    async def complete(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Complete text with exponential backoff on throttling"""
        return await self._call_with_backoff(
            self._complete_text,
            prompt=prompt,
            max_tokens=max_tokens
        )

    async def _complete_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Internal method for actual API call"""
        # Move existing complete() logic here
        # This is the actual API call that might get throttled

    async def generate(
        self, 
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """Generate text with exponential backoff retry"""
        max_retries = 10
        base_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=settings.BEDROCK_MODEL_ID,
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": [{"role": "user", "content": prompt}]
                    })
                )
                
                response_body = json.loads(response.get('body').read())
                return response_body['content'][0]['text']
                
            except (
                self.client.exceptions.ThrottlingException,
                self.client.exceptions.ModelTimeoutException
            ) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries ({max_retries}) exceeded: {str(e)}")
                    raise
                
                delay = (base_delay * 2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {str(e)}")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error generating from LLM: {str(e)}")
                raise 