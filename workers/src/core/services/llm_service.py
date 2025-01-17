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