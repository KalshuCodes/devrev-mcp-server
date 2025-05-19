"""
DevRev API client.

This module provides a client for interacting with the DevRev API.
"""
import logging
from typing import Any, Dict, List, Optional, Union
import time

import requests

from devrev_mcp.errors import DevRevAPIError, handle_api_error
from devrev_mcp.config import config
from devrev_mcp.auth import DevRevAuth

logger = logging.getLogger(__name__)

# Constants from config
API_BASE_URL = config.api.base_url
SEARCH_ENDPOINT = "/search.core"
WORKS_ENDPOINT = "/works.get"
WORKS_LIST_ENDPOINT = "/works.list"
WORKS_CREATE_ENDPOINT = "/works.create"
WORKS_UPDATE_ENDPOINT = "/works.update"
PARTS_ENDPOINT = "/parts.get"
PARTS_LIST_ENDPOINT = "/parts.list"
DEV_USERS_ENDPOINT = "/dev-users.get"
DEV_USER_SELF_ENDPOINT = "/dev-users.self"


class DevRevClient:
    """Client for interacting with the DevRev API."""

    def __init__(self, api_key: str, current_user: Dict[str, Any] = None) -> None:
        """
        Initialize the DevRev client.
        
        Args:
            api_key: DevRev Personal Access Token (PAT)
            current_user: Current user information (if already available from auth)
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self.timeout = config.api.timeout
        self.max_retries = config.api.retries
        self._current_user = current_user
        logger.info("DevRev client initialized")

    async def search(
        self, query: str, namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Search for objects in DevRev.
        
        Args:
            query: Search query
            namespace: Type of objects to search (issue, ticket, article, etc.)
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for '{query}' in namespace '{namespace}'")
        
        # Complete list of valid DevRev namespaces
        valid_namespaces = [
            "account", "article", "capability", "component", "conversation",
            "custom_object", "custom_part", "custom_work", "dashboard", "dev_user",
            "enhancement", "feature", "group", "issue", "linkable", "microservice",
            "object_member", "operation", "opportunity", "part", "product", "project",
            "question_answer", "rev_org", "rev_user", "runnable", "service_account",
            "sys_user", "tag", "task", "ticket", "vista", "workflow", "comment"
        ]
        
        if namespace not in valid_namespaces:
            logger.warning(f"Invalid namespace: {namespace}, defaulting to 'issue'")
            namespace = "issue"
        
        # Map namespace to DevRev's API namespaces format
        namespace_map = {
            "account": "account",
            "article": "artifact",
            "capability": "capability",
            "component": "component",
            "conversation": "conversation",
            "comment": "comment",
            "custom_object": "custom_object",
            "custom_part": "custom_part",
            "custom_work": "custom_work",
            "dashboard": "dashboard",
            "dev_user": "dev_user",
            "enhancement": "enhancement",
            "feature": "feature",
            "group": "group",
            "issue": "issue",
            "linkable": "linkable",
            "microservice": "microservice",
            "object_member": "object_member",
            "operation": "operation",
            "opportunity": "opportunity",
            "part": "part",
            "product": "product",
            "project": "project",
            "question_answer": "question_answer",
            "rev_org": "rev_org",
            "rev_user": "rev_user",
            "runnable": "runnable",
            "service_account": "service_account",
            "sys_user": "sys_user",
            "tag": "tag",
            "task": "task",
            "ticket": "ticket",
            "vista": "vista",
            "workflow": "workflow"
        }
        
        # Build the API endpoint
        endpoint = SEARCH_ENDPOINT
        
        # Using GET request as per documentation
        params = {
            "query": query,
            "namespaces": namespace_map.get(namespace, "issue"),
            "limit": 10
        }
        
        return await self._make_request("GET", endpoint, params=params)
    
    async def list_works(
        self, work_type: str = None, owned_by: str = None, limit: int = 10, applies_to_part: str = None,
        cursor: str = None
    ) -> List[Dict[str, Any]]:
        """
        List works based on specified filters.
        
        Args:
            work_type: The type of work to filter by (issue, ticket, task)
            owned_by: The ID of the user who owns the works.
                      Use "self" to use the current authenticated user.
            limit: Maximum number of items to return
            applies_to_part: The ID of the part that works apply to
            cursor: Pagination cursor for fetching next page of results
            
        Returns:
            List of works matching the criteria
        """
        # If owned_by is "self", use the current user's ID
        actual_owned_by = owned_by
        if owned_by == "self":
            actual_owned_by = self._current_user.get("id")
            logger.info(f"Using current user ID: {actual_owned_by}")
        
        logger.info(f"Listing works of type '{work_type}' owned by '{actual_owned_by}'")
        if applies_to_part:
            logger.info(f"Filtering by applies_to_part: {applies_to_part}")
        if cursor:
            logger.info(f"Using pagination cursor: {cursor}")
        
        # Build the API endpoint with query parameters
        endpoint = WORKS_LIST_ENDPOINT
        params = {}
        
        if work_type:
            params["type"] = work_type
        if actual_owned_by:
            params["owned_by"] = actual_owned_by
        if limit:
            params["limit"] = limit
        if applies_to_part:
            params["applies_to_part"] = applies_to_part
        if cursor:
            params["cursor"] = cursor
            
        return await self._make_request("GET", endpoint, params=params)
            
    async def create_work(
        self, work_type: str, title: str, applies_to_part: Optional[str] = None, body: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new work item (issue or task) in DevRev.
        
        Args:
            work_type: Type of work to create ('issue' or 'task')
            title: Title of the work
            applies_to_part: ID of the part this work applies to (required for issue and ticket types)
            body: Optional body/description of the work
            
        Returns:
            Created work object
        """
        if work_type not in ["issue", "task"]:
            raise ValueError(f"Unsupported work type: {work_type}. Must be 'issue' or 'task'")
        
        # Check if applies_to_part is required based on work_type
        if work_type == "issue" and not applies_to_part:
            raise ValueError("applies_to_part is required for issues")
            
        logger.info(f"Creating {work_type} with title '{title}'")
        
        # Get current user ID for owned_by field
        owned_by = [self._current_user.get("id")] if self._current_user else []
        
        # Build request payload
        payload = {
            "type": work_type,
            "title": title,
            "owned_by": owned_by
        }
        
        # Add applies_to_part if provided
        if applies_to_part:
            payload["applies_to_part"] = applies_to_part
            
        # Add body if provided
        if body:
            payload["body"] = body
        
        return await self._make_request("POST", WORKS_CREATE_ENDPOINT, json=payload)
    
    async def get_part(self, part_id: str) -> Dict[str, Any]:
        """
        Get details about a part by its ID.
        
        Parts can be one of six types: Capability, Enhancement, Feature, 
        Linkable, Runnable, or Product.
        
        Args:
            part_id: ID of the part to get
            
        Returns:
            Part details
        """
        logger.info(f"Getting part with ID: {part_id}")
        
        # Build query params
        params = {
            "id": part_id
        }
        
        return await self._make_request("GET", PARTS_ENDPOINT, params=params)
    
    async def list_parts(
        self, part_type: str, cursor: Optional[str] = None, parent_part: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List parts based on specified filters.
        
        Parts can be one of six types: Capability, Enhancement, Feature, 
        Linkable, Runnable, or Product.
        
        Args:
            part_type: The type of part to filter by (capability, enhancement, feature, etc.)
            cursor: Pagination cursor for fetching next page of results
            parent_part: ID of the parent part to filter children parts
            
        Returns:
            List of parts matching the criteria
        """
        logger.info(f"Listing parts of type '{part_type}'")
        
        # Validate part type (although the API should do this as well)
        valid_types = ["capability", "enhancement", "feature", "linkable", "runnable", "product"]
        if part_type.lower() not in valid_types:
            logger.warning(f"Invalid part type: {part_type}, but proceeding with request")
        
        # Build the API endpoint with query parameters
        params = {
            "type": part_type
        }
        
        # Add optional parameters if provided
        if cursor:
            params["cursor"] = cursor
        
        if parent_part:
            params["parent_part.parts"] = parent_part
            
        return await self._make_request("GET", PARTS_LIST_ENDPOINT, params=params)
        
    async def get_object(self, object_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a DevRev object.
        
        Args:
            object_id: ID of the object (e.g., ISS-123, TKT-456)
            
        Returns:
            Object details
        """
        logger.info(f"Getting object with ID: {object_id}")
        
        # Determine the object type from the ID prefix
        object_type = self._determine_object_type(object_id)
        
        if object_type == "issue":
            endpoint = WORKS_ENDPOINT
        elif object_type == "ticket":
            endpoint = WORKS_ENDPOINT
        elif object_type == "article":
            endpoint = WORKS_ENDPOINT
        elif object_type == "user":
            endpoint = DEV_USERS_ENDPOINT
        else:
            raise ValueError(f"Unsupported object ID format: {object_id}")
        
        return await self._make_request("GET", f"{endpoint}?id={object_id}")

    async def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Make an HTTP request to the DevRev API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            Response data
        """
        url = f"{API_BASE_URL}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("headers", self.headers)
        
        retries = 0
        while retries <= self.max_retries:
            try:
                if method == "GET":
                    response = requests.get(url, **kwargs)
                elif method == "POST":
                    response = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                data = response.json()
                
                # Process the response based on the endpoint
                if endpoint == SEARCH_ENDPOINT:
                    return data.get("results", [])
                elif endpoint == WORKS_LIST_ENDPOINT:
                    return data.get("works", [])
                elif endpoint == WORKS_CREATE_ENDPOINT:
                    return data.get("work", {})
                elif endpoint == WORKS_UPDATE_ENDPOINT:
                    return data.get("work", {})
                elif endpoint == PARTS_ENDPOINT:
                    return data.get("part", {})
                elif endpoint == PARTS_LIST_ENDPOINT:
                    return data.get("parts", [])
                
                return data
                
            except requests.exceptions.RequestException as e:
                # If we've reached the maximum retries, handle the error
                if retries >= self.max_retries:
                    handle_api_error(e)
                
                # Otherwise, retry with exponential backoff
                retries += 1
                wait_time = 2 ** retries  # Exponential backoff
                logger.warning(f"Request failed. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # This should never be reached due to handle_api_error raising an exception
        raise Exception("Maximum retries exceeded")

    def _determine_object_type(self, object_id: str) -> str:
        """
        Determine the object type from its ID.
        
        Args:
            object_id: Object ID (e.g., ISS-123, TKT-456, ART-789)
            
        Returns:
            Object type (issue, ticket, article)
        """
        if object_id.startswith("ISS-"):
            return "issue"
        elif object_id.startswith("TKT-"):
            return "ticket"
        elif object_id.startswith("ART-"):
            return "article"
        elif object_id == "SELF" or object_id.startswith("DEVU-"):
            # Special case for dev-users.self endpoint
            return "user"
        else:
            # If we can't determine the type, try to use the full DON ID
            return "unknown"

    async def update_work(
        self, work_id: str, title: str = None, applies_to_part: Optional[str] = None, 
        body: Optional[str] = None, stage: Optional[str] = None, status: Optional[str] = None
    ) -> Dict[str, Any]:
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
            Updated work object
        """
        logger.info(f"Updating work with ID {work_id}")
        
        # Build request payload with only provided fields
        payload = {
            "id": work_id
        }
        
        if title is not None:
            payload["title"] = title
            
        if applies_to_part is not None:
            payload["applies_to_part"] = applies_to_part
            
        if body is not None:
            payload["body"] = body
            
        if stage is not None:
            payload["stage"] = stage
            
        if status is not None:
            payload["status"] = status
        
        return await self._make_request("POST", WORKS_UPDATE_ENDPOINT, json=payload) 