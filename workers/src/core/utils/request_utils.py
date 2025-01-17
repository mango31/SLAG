import uuid
from datetime import datetime

def generate_request_id() -> str:
    """
    Generate a unique request ID combining timestamp and UUID.
    Format: YYYYMMDD-HHMMSS-uuid4
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}-{unique_id}" 