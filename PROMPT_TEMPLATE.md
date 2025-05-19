# DevRev MCP Workflow Prompt Template

Use this template as a base prompt for creating AI workflows with the DevRev MCP tools. Customize it to fit your specific needs and scenarios.

---

## Base Prompt for DevRev MCP Tools

I need help managing my DevRev objects (products, features, issues, etc.) using the DevRev MCP tools. These tools allow you to interact with the DevRev API to search, list, create, and manage various objects.

Available tools:
- `search`: Search for objects in DevRev
- `list_works`: List works (issues, tickets, tasks) with filters
- `get_object`: Get detailed information about any DevRev object
- `create_work`: Create new work items (issues or tasks)
- `update_work`: Update existing work items (title, status, etc.)
- `get_part`: Get details about a specific part
- `list_parts`: List parts filtered by type and other criteria
- `devrev_context`: Get comprehensive documentation on tool usage

## Workflow Guidelines

When helping me with DevRev tasks:

1. **Think step-by-step**: Break down complex tasks into logical sequences of operations.

2. **Chain tools together**: Use the output of one tool as the input for another when appropriate.

3. **Handle empty results gracefully**: Check if searches or listings return results before proceeding.

4. **Provide context in your recommendations**: Explain why you're suggesting certain actions.

5. **Ask clarifying questions**: If you need more information to proceed with a workflow.

## Example Tasks 

Here are some common tasks where you can help me by chaining these tools together:

1. **Product Exploration**: Help me navigate my product hierarchy to understand how products, features, and issues relate to each other.

2. **Issue Management**: Find, create, and organize issues across different products and features.

3. **Status Reporting**: Generate summaries of work status across different parts of my DevRev organization.

4. **Work Prioritization**: Help me identify high-priority or unassigned work items that need attention.

## Example Tool Usage

```python
# Search for issues with "authentication" in the title or description
results = search(query="authentication", namespace="issue")

# List issues assigned to the current user
works = list_works(work_type="issue", owned_by="self")

# Get details about a specific issue
issue = get_object(id="ISS-123")

# Create a new issue for a feature
new_issue = create_work(
    work_type="issue", 
    title="API returns 500 error", 
    applies_to_part="FEAT-123"
)

# Update an existing issue
updated = update_work(work_id="ISS-456", status="closed")

# Explore product structure
products = list_parts(part_type="product")
```

## Troubleshooting

If you encounter any issues with the DevRev MCP tools:

1. Verify your API key is valid and properly set in the environment
2. Check the logs at `./tmp/logs/devrev_mcp.log` in the current working directory
3. Ensure you're using the correct parameters for each tool call
4. Make sure the DevRev API endpoints are accessible from your network

## Current Task

[DESCRIBE YOUR SPECIFIC TASK HERE]

For example:
- "I need to create a new issue for our authentication feature"
- "Help me find all unassigned issues in our payment service"
- "I want to explore the structure of our product and its features" 