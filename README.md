# DevRev MCP

> **Note:** This is an unofficial implementation of the DevRev Model Context Protocol. It is not created, maintained, or endorsed by DevRev, Inc.

A Cursor Model Context Protocol (MCP) implementation for DevRev integration, allowing AI assistants to interact with the DevRev platform seamlessly.

## Features

- **Search DevRev**: Find objects across multiple namespaces (issues, tickets, articles, etc.)
- **Manage Works**: List, create, and update issues, tickets, and tasks
- **Parts Management**: Explore product hierarchies, capabilities, features, and more
- **Detailed Information**: Retrieve comprehensive object details by ID
- **Cursor Integration**: Ready-to-use with Cursor IDE via SSE transport
- **Robust Error Handling**: Comprehensive logging and error recovery
- **Context-aware Assistance**: Built-in documentation and best practices

## Prerequisites

- Python 3.8+
- DevRev API access token (PAT) with appropriate permissions
- Cursor IDE for optimal integration

## Installation

### Quick Start with Install Script

```bash
./install.sh
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
# Required
export DEVREV_API_KEY="your_devrev_personal_access_token"

# Optional (with defaults shown)
export DEVREV_API_BASE_URL="https://api.devrev.ai"
export DEVREV_API_TIMEOUT="30"
export DEVREV_API_RETRIES="3"
export DEVREV_MCP_HOST="127.0.0.1"
export DEVREV_MCP_PORT="8888"
export DEVREV_MCP_LOG_LEVEL="info"  # debug, info, warning, error
export DEVREV_MCP_DEBUG="false"
```

## Usage

### Starting the Server

```bash
python -m devrev_mcp
```

### Connecting Cursor

In Cursor IDE, open settings and add the MCP server URL:

```
http://127.0.0.1:8888/sse
```

### Available Tools

#### Comprehensive Documentation

Access the built-in documentation with:

```python
context = devrev_context()
```

This provides detailed information on all tools, supported namespaces, parameters, and usage examples.

#### Search DevRev

```python
# Search for issues with "authentication" in the title or description
results = search(query="authentication", namespace="issue")

# Search for features in a specific product
results = search(query="product:payments api", namespace="feature")
```

#### List Works

```python
# List issues assigned to the current user
works = list_works(work_type="issue", owned_by="self", limit=20)

# List tickets related to a specific feature
works = list_works(work_type="ticket", applies_to_part="FEAT-123", limit=10)
```

#### Create Works

```python
# Create a new issue for a specific feature
issue = create_work(
    work_type="issue",
    title="API returns 500 error on large payloads",
    applies_to_part="FEAT-123",
    body="When submitting payloads larger than 1MB, the API consistently returns a 500 error."
)

# Create a new task without part association
task = create_work(
    work_type="task",
    title="Update documentation with new endpoints",
    body="Add the newly created endpoints to our API documentation."
)
```

#### Update Works

```python
# Update an issue's title
updated_issue = update_work(
    work_id="ISS-123",
    title="Updated: API returns 500 error on large payloads"
)

# Change an issue's status
updated_issue = update_work(
    work_id="ISS-123",
    status="closed"
)

# Update multiple fields at once
updated_issue = update_work(
    work_id="ISS-123",
    title="Updated title",
    body="Updated description",
    applies_to_part="FEAT-456",
    stage="done"
)
```

#### Get Object Details

```python
# Get details about an issue
issue = get_object(id="ISS-123")

# Get details about a ticket
ticket = get_object(id="TKT-456")
```

#### Explore Parts

```python
# List all products
products = list_parts(part_type="product")

# List capabilities under a specific product
capabilities = list_parts(part_type="capability", parent_part="PROD-123")

# List features under a capability
features = list_parts(part_type="feature", parent_part="CAP-123")

# Get details about a specific part
part = get_part(id="FEAT-123")
```

## Workflow Examples

### Example 1: Creating an Issue for a Feature

```python
# First, search for the feature or get a list of features
features = list_parts(part_type="feature", parent_part="CAP-123")
feature_id = features["parts"][0]["id"]  # Select the first feature

# Create an issue linked to that feature
new_issue = create_work(
    work_type="issue",
    title="Fix security vulnerability in authentication",
    applies_to_part=feature_id,
    body="Critical security vulnerability in the token validation process."
)

# Verify the issue was created and get full details
created_issue = get_object(id=new_issue["work"]["id"])
```

### Example 2: Hierarchical Product Exploration

```python
# Start with listing all products
products = list_parts(part_type="product")
product_id = products["parts"][0]["id"]  # Select a product

# List capabilities for this product
capabilities = list_parts(part_type="capability", parent_part=product_id)
capability_id = capabilities["parts"][0]["id"]  # Select a capability

# List features under this capability
features = list_parts(part_type="feature", parent_part=capability_id)
feature_id = features["parts"][0]["id"]  # Select a feature

# List issues related to this feature
issues = list_works(work_type="issue", applies_to_part=feature_id)
```

### Example 3: Issue Management Workflow

```python
# Search for a specific issue by keyword
issues = search(query="authentication error", namespace="issue")
issue_id = issues["results"][0]["id"]

# Get full details of the issue
issue = get_object(id=issue_id)

# Update the issue with new information
updated_issue = update_work(
    work_id=issue_id,
    title=f"[In Progress] {issue['title']}",
    stage="in_progress"
)
```

## Supported DevRev Object Types

The integration supports a wide range of DevRev objects, including:

- **Works**: issues, tickets, tasks
- **Parts**: products, capabilities, features, enhancements, linkables, runnables
- **Users**: dev_users, rev_users, sys_users
- **Communication**: conversations, comments, articles
- **And more**: projects, tags, workflows, etc.

For the complete list of supported objects and their usage, refer to the `devrev_context()` tool output.

## Troubleshooting

If you encounter issues with the MCP tools:

1. Verify your API key is valid and properly set
2. Check the logs at `./tmp/logs/devrev_mcp.log`
3. Ensure you're using the correct parameters for each tool
4. Check that the DevRev API endpoints are accessible from your network

## Development

### Project Structure

```
devrev_mcp/
├── src/
│   └── devrev_mcp/
│       ├── __init__.py
│       ├── __main__.py     # Entry point
│       ├── auth.py         # Authentication
│       ├── client.py       # DevRev API client
│       ├── config.py       # Configuration
│       ├── errors.py       # Error handling
│       └── sse.py          # SSE transport
├── README.md               # This file
└── pyproject.toml          # Project metadata
```

### Running Tests

```bash
pytest
```

## License

MIT

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to help improve this integration.

## Acknowledgments

- DevRev API team for their excellent documentation and support
- Cursor team for the MCP framework
- All contributors to this project
