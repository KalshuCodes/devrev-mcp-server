"""
Error handling utilities for DevRev API.
"""
import logging
import json
from typing import Dict, Optional, Any, Tuple

import requests

logger = logging.getLogger(__name__)


class DevRevAPIError(Exception):
    """Exception raised for errors in the DevRev API."""
    
    def __init__(self, message: str, status_code: int, response_body: Optional[str] = None) -> None:
        """
        Initialize a new DevRevAPIError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Raw response body from the API
        """
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.error_details = self._parse_error_details(response_body)
        super().__init__(self.message)
    
    def _parse_error_details(self, response_body: Optional[str]) -> Dict[str, Any]:
        """
        Parse error details from the response body.
        
        Args:
            response_body: Raw response body from the API
            
        Returns:
            Parsed error details
        """
        if not response_body:
            return {}
            
        try:
            data = json.loads(response_body)
            if isinstance(data, dict):
                return data
            return {"raw_error": data}
        except json.JSONDecodeError:
            return {"raw_error": response_body}
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_details:
            return f"{self.message} (Status: {self.status_code}): {self.error_details}"
        return f"{self.message} (Status: {self.status_code})"


def handle_api_error(error: requests.exceptions.RequestException) -> Tuple[str, int]:
    """
    Handle request exceptions and return a standardized error message and status code.
    
    Args:
        error: Request exception
        
    Returns:
        Tuple of (error_message, status_code)
    """
    status_code = 500  # Default to internal server error
    message = "An error occurred while communicating with the DevRev API"
    
    if hasattr(error, "response") and error.response is not None:
        status_code = error.response.status_code
        response_body = getattr(error.response, "text", "")
        
        # Try to extract more specific error information
        try:
            error_data = error.response.json()
            if "message" in error_data:
                message = error_data["message"]
            elif "error" in error_data:
                message = error_data["error"]
        except (json.JSONDecodeError, ValueError, AttributeError):
            # If we can't parse JSON, use the status code to provide info
            if status_code == 401:
                message = "Authentication failed. Please check your API key."
            elif status_code == 403:
                message = "You don't have permission to access this resource."
            elif status_code == 404:
                message = "The requested resource was not found."
            elif status_code == 429:
                message = "Rate limit exceeded. Please try again later."
            
        # Log detailed information about the error
        logger.error(f"API error: {message} (Status: {status_code})")
        logger.debug(f"Response body: {response_body}")
        
        # Raise a structured exception
        raise DevRevAPIError(message, status_code, response_body)
    
    # For network or connection errors
    logger.error(f"Network error: {str(error)}")
    return "Could not connect to DevRev API. Please check your internet connection.", 503 