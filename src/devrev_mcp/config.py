"""
Configuration module for DevRev MCP server.

This module handles configuration loading and validation.
"""
import os
import logging
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ServerConfig(BaseModel):
    """Server configuration model."""
    
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8888)
    log_level: str = Field(default="info")
    debug: bool = Field(default=False)


class APIConfig(BaseModel):
    """API configuration model."""
    
    base_url: str = Field(default="https://api.devrev.ai")
    timeout: int = Field(default=10)  # Request timeout in seconds
    retries: int = Field(default=3)   # Number of retry attempts


class Config(BaseModel):
    """Main configuration model."""
    
    server: ServerConfig = Field(default_factory=ServerConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    api_key: Optional[str] = None


def load_config() -> Config:
    """
    Load configuration from environment variables.
    
    Returns:
        Config: Configuration object
    """
    # Get DevRev API key from environment
    api_key = os.environ.get("DEVREV_API_KEY")
    
    # Get server configuration from environment
    server_config = ServerConfig(
        host=os.environ.get("DEVREV_MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("DEVREV_MCP_PORT", "8888")),
        log_level=os.environ.get("DEVREV_MCP_LOG_LEVEL", "info"),
        debug=os.environ.get("DEVREV_MCP_DEBUG", "").lower() in ("true", "1", "yes"),
    )
    
    # Get API configuration from environment
    api_config = APIConfig(
        base_url=os.environ.get("DEVREV_API_BASE_URL", "https://api.devrev.ai"),
        timeout=int(os.environ.get("DEVREV_API_TIMEOUT", "30")),
        retries=int(os.environ.get("DEVREV_API_RETRIES", "3")),
    )
    
    return Config(
        server=server_config,
        api=api_config,
        api_key=api_key,
    )


# Global configuration instance
config = load_config() 