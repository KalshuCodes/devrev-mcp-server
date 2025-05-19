"""
Authentication handling for DevRev API.
"""
import logging
import requests
from typing import Dict, Any, Optional
import time

from devrev_mcp.config import config
from devrev_mcp.errors import DevRevAPIError, handle_api_error

logger = logging.getLogger(__name__)

# Constants
API_BASE_URL = config.api.base_url
DEV_USER_SELF_ENDPOINT = "/dev-users.self"


class DevRevAuth:
    """Handler for DevRev authentication."""
    
    @staticmethod
    def validate_token(api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate the DevRev API key by requesting the current user's information.
        
        Args:
            api_key: DevRev Personal Access Token (PAT)
            
        Returns:
            User information if token is valid, None otherwise
        """
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        
        # Set up retry mechanism
        max_retries = config.api.retries
        timeout = config.api.timeout
        
        for attempt in range(max_retries + 1):
            try:
                response = requests.get(
                    f"{API_BASE_URL}{DEV_USER_SELF_ENDPOINT}",
                    headers=headers,
                    timeout=timeout
                )
                
                response.raise_for_status()
                user_data = response.json()
                
                logger.info("Token validated successfully")
                return user_data.get("dev_user")
            except requests.exceptions.RequestException as e:
                # If it's the last attempt, return None
                if attempt == max_retries:
                    logger.error(f"Token validation failed after {max_retries + 1} attempts: {str(e)}")
                    if hasattr(e, "response") and hasattr(e.response, "text"):
                        logger.error(f"Response: {e.response.text}")
                    return None
                
                # Otherwise, retry with exponential backoff
                wait_time = 2 ** attempt
                logger.warning(f"Token validation failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time) 