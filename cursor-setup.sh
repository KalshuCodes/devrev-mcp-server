#!/bin/bash

# DevRev MCP Server Setup Script for Cursor IDE

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}DevRev MCP Server Setup for Cursor IDE${NC}"
echo -e "======================================\n"

# Get absolute path to the installation directory
INSTALL_DIR=$(cd "$(dirname "$0")" && pwd)
VENV_PATH="$INSTALL_DIR/venv"
SERVER_PATH="$VENV_PATH/bin/devrev-mcp"

if [ ! -f "$SERVER_PATH" ]; then
    echo -e "${YELLOW}Server executable not found at $SERVER_PATH${NC}"
    echo -e "${YELLOW}Make sure you've run install.sh first.${NC}\n"
    exit 1
fi

echo -e "${GREEN}✓ Found DevRev MCP server at: $SERVER_PATH${NC}\n"

# Prompt for API key
echo -e "${BOLD}Enter your DevRev API key:${NC} "
read -s API_KEY
echo -e "\n"

if [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API key cannot be empty.${NC}"
    exit 1
fi

# Create Cursor configuration
echo -e "${BOLD}Setting up Cursor IDE integration...${NC}\n"

# Create a temporary JSON file to be pasted into Cursor settings
cat > "$INSTALL_DIR/cursor_devrev_config.json" << EOL
{
  "mcpServers": {
    "devrev": {
      "command": "$SERVER_PATH",
      "env": {
        "DEVREV_API_KEY": "$API_KEY",
        "DEVREV_MCP_HOST": "127.0.0.1",
        "DEVREV_MCP_PORT": "8888",
        "DEVREV_MCP_LOG_LEVEL": "info"
      }
    }
  }
}
EOL

echo -e "${GREEN}${BOLD}✓ Configuration created!${NC}\n"
echo -e "${BOLD}To complete setup:${NC}\n"

echo -e "${YELLOW}1. Open Cursor IDE${NC}"
echo -e "${YELLOW}2. Go to Settings > Extensions > Model Context Protocol${NC}"
echo -e "${YELLOW}3. Add a new MCP server with the following details:${NC}\n"

echo -e "   Name: ${BOLD}devrev${NC}"
echo -e "   Command: ${BOLD}$SERVER_PATH${NC}"
echo -e "   Environment Variables:"
echo -e "   - ${BOLD}DEVREV_API_KEY=${NC}[your API key]"
echo -e "   - (Optional) ${BOLD}DEVREV_MCP_LOG_LEVEL=debug${NC} for more detailed logs\n"

echo -e "Alternatively, you can use the configurations saved in:"
echo -e "${BOLD}$INSTALL_DIR/cursor_devrev_config.json${NC}\n"

echo -e "${GREEN}${BOLD}Happy coding with DevRev MCP and Cursor!${NC}"

# Check if DEVREV_API_KEY is set
if [ -z "$DEVREV_API_KEY" ]; then
    echo -e "\n${RED}Error: DEVREV_API_KEY environment variable is not set${NC}"
    echo -e "Please set it with: ${YELLOW}export DEVREV_API_KEY=your_api_key_here${NC}"
    exit 1
fi

# Check if venv exists, create if not
echo -e "\n${BOLD}Checking virtual environment...${NC}"

# Check Python version first
PY_VERSION=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
MAJOR=$(echo $PY_VERSION | cut -d. -f1)
MINOR=$(echo $PY_VERSION | cut -d. -f2)

# Compare the version properly - ensure Python 3.7+ but handle Python 3.10+ correctly
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ is required, but you have Python $PY_VERSION${NC}"
    echo -e "Please upgrade your Python installation and try again"
    exit 1
fi
echo -e "Found Python $PY_VERSION ${GREEN}✓${NC}"

if [ ! -d "venv" ]; then
    echo -e "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install the package in development mode
echo -e "\n${BOLD}Installing DevRev MCP...${NC}"
pip install -e .
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install DevRev MCP.${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p ./tmp/logs

# Get the host and port from config or use defaults
HOST="127.0.0.1"
PORT="8888"

echo -e "\n${GREEN}${BOLD}DevRev MCP is installed!${NC}"
echo -e "\n${BOLD}Starting DevRev MCP server...${NC}"
echo -e "The server will run in the foreground. Press Ctrl+C to stop.\n"

# Show Cursor setup instructions
echo -e "${YELLOW}${BOLD}======= CURSOR SETUP INSTRUCTIONS =======${NC}"
echo -e "1. Open Cursor"
echo -e "2. Go to Settings → AI → Custom Tools"
echo -e "3. Add a new tool with the URL:"
echo -e "${GREEN}   http://${HOST}:${PORT}/sse${NC}"
echo -e "4. Save the settings"
echo -e "5. Restart Cursor to ensure the changes take effect"
echo -e "${YELLOW}=======================================${NC}\n"

echo -e "${RED}IMPORTANT:${NC} If you continue to see errors about 'unknown message ID', try:"
echo -e "- Ensuring no other DevRev MCP servers are running"
echo -e "- Check the logs in this terminal for connection information"
echo -e "- Confirm your firewall isn't blocking connections on port ${PORT}"
echo -e "${GREEN}Server logs will be available at: ${BOLD}./tmp/logs/${NC}\n"

# Run the server
python -m devrev_mcp 