import boto3
from datetime import datetime
import logging
from src.worker.config import settings

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.s3 = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket = settings.STORY_BUCKET
        logger.info(f"Initialized S3Service with bucket: {self.bucket}")

    async def save_story(self, content: str, story_id: str, story_type: str, format: str = "md") -> str:
        """
        Save content to S3 and return the URL
        format: "md" or "txt" or "json"
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            key = f"{story_type}/{story_id}-{timestamp}.{format}"
            
            # Upload to S3
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType='text/markdown' if format == 'md' else 'text/plain'
            )
            
            # Generate URL
            url = f"s3://{self.bucket}/{key}"
            logger.info(f"Saved {story_type} to {url}")
            return url
            
        except Exception as e:
            logger.error(f"Error saving to S3: {str(e)}")
            raise 