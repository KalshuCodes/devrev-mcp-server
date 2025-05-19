"""
Main entry point for the DevRev MCP server.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Union
import json

from fastmcp import FastMCP
# Remove BaseModel import as we'll use raw dictionaries instead
# from pydantic import BaseModel

from devrev_mcp.client import DevRevClient
from devrev_mcp.auth import DevRevAuth
from devrev_mcp.errors import DevRevAPIError
from devrev_mcp.config import config

# Set up logging with both console and file outputs
log_level = getattr(logging, config.server.log_level.upper(), logging.INFO)

# Create logs directory if it doesn't exist
log_dir = Path(os.getcwd()) / "tmp" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Log file path with timestamp to avoid conflicts
log_file = log_dir / f"devrev_mcp.log"

# Set up root logger
logger = logging.getLogger()
logger.setLevel(log_level)

# Clear any existing handlers
if logger.handlers:
    logger.handlers.clear()

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)

# File handler with rotation (10 MB max size, 5 backup files)
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
    encoding="utf-8"
)
file_handler.setLevel(log_level)
file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Get module-specific logger
module_logger = logging.getLogger(__name__)
module_logger.info(f"Logging to file: {log_file}")

# Initialize the DevRev MCP server
mcp = FastMCP("DevRev", 
              description="Model Context Protocol server for DevRev",
              debug=config.server.debug)

client: Optional[DevRevClient] = None

# Remove Pydantic models and use raw parameter handling instead

def on_connect() -> None:
    """Handle connection events."""
    global client

    # Check if API key is set
    if not config.api_key:
        logger.error("DEVREV_API_KEY environment variable not set")
        sys.exit(1)
    
    # Validate the token and get user information
    user_info = DevRevAuth.validate_token(config.api_key)
    if not user_info:
        logger.error("Invalid DevRev API key")
        sys.exit(1)
    
    logger.info(f"Authenticated as: {user_info.get('display_name', 'Unknown User')}")
    
    # Initialize client with the user information
    client = DevRevClient(config.api_key, current_user=user_info)
    


@mcp.tool()
async def search(query: str, namespace: str) -> Dict[str, Any]:
    """
    Search DevRev using the provided query.
    
    Args:
        query: The search query to look for
        namespace: Type of objects to search (issue, ticket, article)
        
    Returns:
        Search results from DevRev
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Searching DevRev with query: {query} (namespace: {namespace})")
    
    try:
        results = await client.search(query, namespace)
        logger.info(f"Found {len(results)} results")
        return {"results": results}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error searching DevRev: {str(e)}")
        raise ValueError(f"Error searching DevRev: {str(e)}")


@mcp.tool()
async def list_works(work_type: str = None, owned_by: str = None, limit: int = 10, applies_to_part: str = None, cursor: str = None) -> Dict[str, Any]:
    """
    List works in DevRev based on specified filters.
    
    Args:
        work_type: The type of work to filter by (issue, ticket, task)
        owned_by: The ID of the user who owns the works. Use "self" for current user.
        limit: Maximum number of items to return
        applies_to_part: The ID of the part that works apply to
        cursor: Pagination cursor for fetching next page of results
        
    Returns:
        List of works matching the criteria
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Listing works of type: {work_type}, owned by: {owned_by}")
    if applies_to_part:
        logger.info(f"Filtering by applies_to_part: {applies_to_part}")
    if cursor:
        logger.info(f"Using pagination cursor: {cursor}")
    
    try:
        works = await client.list_works(work_type, owned_by, limit, applies_to_part, cursor)
        logger.info(f"Found {len(works)} works")
        return {"works": works}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing works: {str(e)}")
        raise ValueError(f"Error listing works: {str(e)}")


@mcp.tool()
async def get_object(id: str) -> Dict[str, Any]:
    """
    Get all information about a DevRev object using its ID.
    
    Args:
        id: The ID of the DevRev object (e.g., ISS-123, TKT-456)
        
    Returns:
        Object details from DevRev
    """
    global client
    
    if client is None:
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Getting DevRev object with ID: {id}")
    
    try:
        object_details = await client.get_object(id)
        return object_details
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting DevRev object: {str(e)}")
        raise ValueError(f"Error getting DevRev object: {str(e)}")


@mcp.tool()
async def create_work(work_type: str, title: str, applies_to_part: str = None, body: str = None) -> Dict[str, Any]:
    """
    Create a new work item (issue or task) in DevRev.
    
    Args:
        work_type: Type of work to create ('issue' or 'task')
        title: Title of the work
        applies_to_part: ID of the part this work applies to (required for issue type, optional for task)
        body: Optional body/description of the work
        
    Returns:
        Created work object from DevRev
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Creating new {work_type} with title: {title}")
    
    try:
        work = await client.create_work(work_type, title, applies_to_part, body)
        logger.info(f"Successfully created {work_type} with ID: {work.get('id', 'unknown')}")
        return {"work": work}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating work: {str(e)}")
        raise ValueError(f"Error creating work: {str(e)}")


@mcp.tool()
async def get_part(id: str) -> Dict[str, Any]:
    """
    Get details about a part by its ID.
    
    Args:
        id: The ID of the part (e.g., CAP-123, FEAT-456)
        
    Returns:
        Part details from DevRev
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Getting part with ID: {id}")
    
    try:
        part_details = await client.get_part(id)
        logger.info(f"Successfully retrieved part with ID: {id}")
        return {"part": part_details}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting part: {str(e)}")
        raise ValueError(f"Error getting part: {str(e)}")


@mcp.tool()
async def list_parts(part_type: str, cursor: str = None, parent_part: str = None) -> Dict[str, Any]:
    """
    List parts in DevRev based on specified filters.
    
    Args:
        part_type: The type of part to filter by (capability, enhancement, feature, linkable, runnable, product)
        cursor: Pagination cursor for fetching next page of results
        parent_part: ID of the parent part to filter children parts
        
    Returns:
        List of parts matching the criteria
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Listing parts of type: {part_type}")
    
    try:
        parts = await client.list_parts(part_type, cursor, parent_part)
        logger.info(f"Found {len(parts)} parts of type: {part_type}")
        return {"parts": parts}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing parts: {str(e)}")
        raise ValueError(f"Error listing parts: {str(e)}")


@mcp.tool()
async def devrev_context() -> Dict[str, Any]:
    """
    Get detailed information on how to use the DevRev MCP tools and best practices.
    
    Returns:
        Documentation and usage examples for DevRev MCP tools
    """
    logger.info("DevRev context information requested")
    
    return {
        "title": "DevRev MCP Tools Guide",
        "description": "This guide provides information on how to effectively use the DevRev MCP tools for interacting with the DevRev platform.",
        "authentication": {
            "info": "All tools require a valid DevRev API key set as DEVREV_API_KEY environment variable.",
            "validation": "Authentication is automatically validated when connecting to the MCP server."
        },
        "available_tools": [
            {
                "name": "search",
                "description": "Search for objects in DevRev using a query string",
                "parameters": {
                    "query": "Search query string",
                    "namespace": "Type of objects to search (issue, ticket, article, etc.)"
                },
                "supported_namespaces": [
                    "account", "article", "capability", "component", "conversation",
                    "custom_object", "custom_part", "custom_work", "dashboard", "dev_user",
                    "enhancement", "feature", "group", "issue", "linkable", "microservice",
                    "object_member", "operation", "opportunity", "part", "product", "project",
                    "question_answer", "rev_org", "rev_user", "runnable", "service_account",
                    "sys_user", "tag", "task", "ticket", "vista", "workflow", "comment"
                ],
                "examples": [
                    "Search for all open issues: search('status:open', 'issue')",
                    "Search for tickets assigned to me: search('owned_by:me', 'ticket')",
                    "Search for a specific feature: search('authentication feature', 'feature')"
                ]
            },
            {
                "name": "list_works",
                "description": "List works in DevRev based on specified filters",
                "parameters": {
                    "work_type": "Type of work to filter by (issue, ticket, task)",
                    "owned_by": "ID of the user who owns the works. Use 'self' for current user.",
                    "limit": "Maximum number of items to return (default: 10)",
                    "applies_to_part": "ID of the part that works apply to (e.g., FEAT-123)",
                    "cursor": "Pagination cursor for fetching next page of results"
                },
                "examples": [
                    "List issues assigned to me: list_works('issue', 'self')",
                    "List tickets for a specific feature: list_works('ticket', None, 10, 'FEAT-123')",
                    "List all tasks with a limit of 5: list_works('task', None, 5)",
                    "Paginate through results: list_works('issue', 'self', 10, None, 'cursor_token_from_previous_response')"
                ]
            },
            {
                "name": "get_object",
                "description": "Get detailed information about a specific DevRev object",
                "parameters": {
                    "id": "The ID of the object (e.g., ISS-123, TKT-456, ART-789)"
                },
                "examples": [
                    "Get details about an issue: get_object('ISS-123')",
                    "Get details about a ticket: get_object('TKT-456')"
                ]
            },
            {
                "name": "create_work",
                "description": "Create a new work item (issue or task) in DevRev",
                "parameters": {
                    "work_type": "Type of work to create ('issue' or 'task')",
                    "title": "Title of the work",
                    "applies_to_part": "ID of the part this work applies to (required for issue type, optional for task)",
                    "body": "Optional body/description of the work"
                },
                "examples": [
                    "Create a new issue: create_work('issue', 'API fails with 500 error', 'FEAT-123', 'Detailed description of the issue')",
                    "Create a new task: create_work('task', 'Update documentation', null, 'Task without part association')"
                ]
            },
            {
                "name": "update_work",
                "description": "Update an existing work item in DevRev",
                "parameters": {
                    "work_id": "ID of the work to update (e.g., ISS-123, TKT-456)",
                    "title": "New title for the work (optional)",
                    "applies_to_part": "ID of the part this work applies to (optional)",
                    "body": "New body/description of the work (optional)",
                    "stage": "New stage of the work (optional)",
                    "status": "New status of the work (optional)"
                },
                "examples": [
                    "Update issue title: update_work('ISS-123', 'Updated title for API issue')",
                    "Change issue status: update_work('ISS-123', status='closed')",
                    "Update task details: update_work('TKT-456', applies_to_part='FEAT-789', body='Updated description')"
                ]
            },
            {
                "name": "get_part",
                "description": "Get details about a part by its ID",
                "parameters": {
                    "id": "The ID of the part (e.g., CAP-123, FEAT-456)"
                },
                "examples": [
                    "Get details about a feature: get_part('FEAT-123')",
                    "Get details about a capability: get_part('CAP-456')"
                ]
            },
            {
                "name": "list_parts",
                "description": "List parts in DevRev based on specified filters",
                "parameters": {
                    "part_type": "The type of part to filter by (capability, enhancement, feature, linkable, runnable, product)",
                    "cursor": "Pagination cursor for fetching next page of results",
                    "parent_part": "ID of the parent part to filter children parts"
                },
                "supported_part_types": [
                    "capability", "enhancement", "feature", "linkable", "runnable", "product"
                ],
                "examples": [
                    "List all features: list_parts('feature')",
                    "List capabilities under a product: list_parts('capability', None, 'PROD-123')",
                    "List enhancements for a feature: list_parts('enhancement', None, 'FEAT-456')"
                ]
            }
        ],
        "namespace_details": {
            "description": "DevRev supports various object types (namespaces) that can be used with the search tool",
            "namespace_categories": {
                "work_items": ["issue", "ticket", "task"],
                "parts": ["capability", "enhancement", "feature", "linkable", "runnable", "product"],
                "users_and_groups": ["dev_user", "rev_user", "sys_user", "group", "service_account"],
                "organizations": ["rev_org", "account"],
                "communication": ["conversation", "comment", "question_answer", "article"],
                "architecture": ["component", "microservice"],
                "management": ["project", "operation", "opportunity", "dashboard", "workflow", "vista", "tag"],
                "custom_objects": ["custom_object", "custom_part", "custom_work"]
            },
            "common_query_patterns": {
                "status": "status:open, status:closed",
                "owner": "owned_by:me, owned_by:DEVU-123",
                "creator": "created_by:me, created_by:DEVU-123",
                "date_filters": "created_date>2023-01-01, modified_date<2023-12-31",
                "text_search": "Authentication API failure",
                "combined": "status:open owned_by:me authentication"
            }
        },
        "workflows": {
            "finding_relevant_objects": {
                "description": "How to find relevant objects in DevRev",
                "steps": [
                    "Use search() to find objects matching specific criteria",
                    "Use list_parts() to browse the product hierarchy",
                    "Use list_works() to see issues/tickets related to specific parts"
                ]
            },
            "creating_issues": {
                "description": "Process for creating a new issue",
                "steps": [
                    "Find the appropriate part (feature/product) using list_parts() or search()",
                    "Create the issue with create_work() specifying the part ID",
                    "Verify the issue was created using get_object() with the returned ID"
                ]
            },
            "exploring_product_hierarchy": {
                "description": "How to navigate the product structure",
                "steps": [
                    "Start with list_parts('product') to see all products",
                    "Ask the user to provide you the product they work with",
                    "For a specific product, use list_parts('capability', None, 'PROD-123')",
                    "Then ask the user to provide you the capability they work with",
                    "For a capability, use list_parts('feature', None, 'CAP-456') to get all the features",
                    "Ask the user to provide you the feature they work with",
                    "For a feature, use list_parts('enhancement', None, 'FEAT-789') to get all the enhancements",
                    "Ask the user about the enhancement they work with"
                ]
            },
            "working_with_enhancements": {
                "description": "How to get your work done with enhancements ?",
                "steps": [
                    "Use list_works('issue|task|ticket', 'self', 10, 'ENH-123') to get all your works for a enhancement",
                    "Use list_works('issue|task|ticket', None, 10, 'ENH-123') to get all works present for a enhancement",
                    "Use the cursor details to get the next page of works with the same query",
                    "Ask the user about the tasks they work with",
                    "Use create_work('task', 'Task title', 'ENH-123') to create a new task for the enhancement",
                    "Use update_work('TASK-123', 'Task title', 'ENH-123') to update the task for the enhancement",
                    "Use get_object('TASK-123') to get the details of the task",
                ]
            }
        },
        "best_practices": [
            "Use specific search queries to narrow down results",
            "Filter works by applies_to_part when you want to focus on a specific feature or product area",
            "When creating works, provide detailed descriptions to help with resolution",
            "Use the part hierarchy (product > capability > feature > enhancement) when exploring the product structure",
            "Refine search results by combining multiple criteria (e.g., 'status:open owned_by:me')"
        ],
        "common_issues": {
            "authentication_errors": "Ensure your DevRev API key is valid and properly set as an environment variable",
            "not_found_errors": "Double-check object IDs for typos. IDs are case-sensitive.",
            "permission_errors": "Ensure you have appropriate permissions for the actions you're trying to perform",
            "search_not_returning_expected_results": "Try simplifying the search query or using different terms"
        }
    }


@mcp.tool()
async def update_work(work_id: str, title: str = None, applies_to_part: str = None, body: str = None, stage: str = None, status: str = None) -> Dict[str, Any]:
    """
    Update an existing work item in DevRev.
    
    Args:
        work_id: ID of the work to update (e.g., ISS-123, TKT-456)
        title: New title for the work (optional)
        applies_to_part: ID of the part this work applies to (optional)
        body: New body/description of the work (optional)
        stage: New stage of the work (optional)
        status: New status of the work (optional)
        
    Returns:
        Updated work object from DevRev
    """
    global client
    
    if client is None:
        logger.error("DevRev client not initialized")
        raise ValueError("DevRev client not initialized")
    
    logger.info(f"Updating work with ID: {work_id}")
    
    try:
        work = await client.update_work(work_id, title, applies_to_part, body, stage, status)
        logger.info(f"Successfully updated work with ID: {work_id}")
        return {"work": work}
    except DevRevAPIError as e:
        logger.error(f"DevRev API error: {str(e)}")
        raise ValueError(f"DevRev API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating work: {str(e)}")
        raise ValueError(f"Error updating work: {str(e)}")


async def debug_info() -> Dict[str, Any]:
    """
    Provide debug information about the server.
    
    Returns:
        Debug information
    """
    logger.info("Debug endpoint called")
    
    # Test connection to the port to check if it's accessible
    import socket
    port_accessible = True
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((config.server.host, config.server.port))
        s.close()
    except:
        port_accessible = False
    
    # Check if token is valid
    token_valid = False
    if config.api_key:
        user_info = DevRevAuth.validate_token(config.api_key)
        token_valid = user_info is not None
    
    return {
        "status": "running",
        "server": "DevRev MCP",
        "version": "0.1.0",
        "authenticated": client is not None,
        "cursor_integration": {
            "sse_url": f"http://{config.server.host}:{config.server.port}/sse",
            "port_accessible": port_accessible,
            "host": config.server.host,
            "port": config.server.port,
            "token_valid": token_valid
        },
        "tools_provided": [
            {
                "name": "search",
                "description": "Search DevRev using the provided query"
            },
            {
                "name": "list_works", 
                "description": "List works in DevRev based on specified filters"
            },
            {
                "name": "get_object", 
                "description": "Get all information about a DevRev object using its ID"
            },
            {
                "name": "create_work", 
                "description": "Create a new work item (issue or task) in DevRev"
            },
            {
                "name": "update_work",
                "description": "Update an existing work item in DevRev"
            },
            {
                "name": "get_part", 
                "description": "Get details about a part by its ID"
            },
            {
                "name": "list_parts",
                "description": "List parts in DevRev based on specified filters"
            },
            {
                "name": "devrev_context",
                "description": "Get detailed information on how to use the DevRev MCP tools and best practices"
            }
        ],
        "logs_location": str(log_dir),
        "troubleshooting_tips": [
            "Make sure your API key is valid",
            "Ensure no other service is running on port " + str(config.server.port),
            "Check that Cursor is connecting to the correct SSE endpoint URL",
            "Try restarting both the server and Cursor"
        ]
    }


def main() -> None:
    """Run the MCP server."""
    logger.info(f"Starting DevRev MCP server on {config.server.host}:{config.server.port}")
    on_connect()
   
    # Initialize the client immediately if API key is available
    
    # Start the server with SSE transport as recommended by the example
    mcp.run(
        transport="sse",
        port=config.server.port
    )
    logger.info(f"DevRev MCP server started on {config.server.host}:{config.server.port}")
    logger.info(f"Cursor integration available at http://{config.server.host}:{config.server.port}/sse")


if __name__ == "__main__":
    main() 