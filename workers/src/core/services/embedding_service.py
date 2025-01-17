from typing import List
import numpy as np
import boto3
from botocore.config import Config
import json
from src.worker.config import settings
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        config = Config(
            retries=dict(
                max_attempts=10,
                mode='adaptive'
            )
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            region_name=settings.AWS_REGION,
            config=config
        )

    async def get_embedding(self, text: str) -> List[float]:
        """Get embeddings from Bedrock"""
        try:
            response = self.client.invoke_model(
                modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
                body=json.dumps({
                    "inputText": text
                })
            )
            
            response_body = json.loads(response.get('body').read())
            return response_body['embedding']
            
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            try:
                embedding = await self.get_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error getting embedding for text: {text[:100]}... Error: {str(e)}")
                continue
        return embeddings 