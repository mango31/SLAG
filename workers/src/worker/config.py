from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS Settings
    AWS_REGION: str = "us-west-2"
    AWS_PARAMETER_PATH: str = "/vMini-engine/prod"
    STORY_BUCKET: str = "vmini-engine-stories-production"
    
    # Redis Settings
    REDIS_HOST: str = "vmini-engine-redis-production.drxrzz.0001.usw2.cache.amazonaws.com"
    REDIS_PORT: int = 6379
    REDIS_SSL: bool = False
    REDIS_TIMEOUT: int = 10
    
    # Worker Settings
    NUM_WORKERS: int = 4
    ENVIRONMENT: str = "production"
    
    # Bedrock Settings
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    BEDROCK_EMBEDDING_MODEL_ID: str = "amazon.titan-embed-text-v1"

    # Add these LLM Generation Settings
    WORLD_BUILDING_TEMPERATURE: float = 0.3
    WORLD_BUILDING_MAX_TOKENS: int = 200000
    
    FRAMEWORK_TEMPERATURE: float = 0.6
    FRAMEWORK_MAX_TOKENS: int = 200000

    STORY_TEMPERATURE: float = 0.8
    STORY_MAX_TOKENS: int = 200000
    SECTION_MAX_TOKENS: int = 200000
    
    TOP_P: float = 0.9
    
    IMPROVEMENT_TEMPERATURE: float = 0.8
    IMPROVEMENT_MAX_TOKENS: int = 200000

settings = Settings() 