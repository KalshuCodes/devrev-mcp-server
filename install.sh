#!/bin/bash

# DevRev MCP Server Installation Script

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}DevRev MCP Server Installation${NC}"
echo -e "=============================\n"

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3 is installed
echo -e "\n${BOLD}Checking dependencies...${NC}"
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo -e "Please install Python 3.10+ and try again"
    exit 1
fi

# Check Python version
PY_VERSION=$(python3 -c "import sys; print('{}.{}'.format(sys.version_info.major, sys.version_info.minor))")
MAJOR=$(echo $PY_VERSION | cut -d. -f1)
MINOR=$(echo $PY_VERSION | cut -d. -f2)

# Compare the version properly - use numeric comparison to handle Python 3.10+
if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ is required, but you have Python $PY_VERSION${NC}"
    echo -e "Please upgrade your Python installation and try again"
    exit 1
fi
echo -e "Found Python $PY_VERSION ${GREEN}✓${NC}"

# Check for pip
if ! command_exists pip3; then
    echo -e "${RED}Error: pip3 is not installed${NC}"
    echo -e "Please install pip for Python 3 and try again"
    exit 1
fi
echo -e "Found pip3 ${GREEN}✓${NC}"

# Check for venv module
python3 -c "import venv" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: venv module is not available${NC}"
    echo -e "Please install the venv module for Python 3 and try again"
    exit 1
fi
echo -e "Found venv module ${GREEN}✓${NC}"

# Create virtual environment
echo -e "\n${BOLD}Setting up virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "Created virtual environment ${GREEN}✓${NC}"
fi

# Activate virtual environment
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to activate virtual environment${NC}"
    exit 1
fi
echo -e "Activated virtual environment ${GREEN}✓${NC}"

# Install the package
echo -e "\n${BOLD}Installing DevRev MCP...${NC}"

# Install fastmcp first
pip install fastmcp>=0.2.0
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install fastmcp dependency${NC}"
    exit 1
fi
echo -e "Installed fastmcp dependency ${GREEN}✓${NC}"

# Install the package in development mode
pip install -e .
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install DevRev MCP${NC}"
    exit 1
fi
echo -e "Installed DevRev MCP ${GREEN}✓${NC}"

# Make the setup script executable
chmod +x cursor-setup.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to make cursor-setup.sh executable${NC}"
    exit 1
fi

# Create the logs directory
echo -e "\n${BOLD}Creating log directory...${NC}"
mkdir -p ./tmp/logs
echo -e "Created log directory ${GREEN}✓${NC}"

# Installation complete
echo -e "\n${GREEN}${BOLD}DevRev MCP has been successfully installed!${NC}"
echo -e "\nTo start the service and connect with Cursor, run:"
echo -e "${YELLOW}./cursor-setup.sh${NC}"
echo -e "\nBefore running, make sure to set your DevRev API key:"
echo -e "${YELLOW}export DEVREV_API_KEY=your_api_key_here${NC}"

# Deactivate the virtual environment
deactivate

# Configure the API key
echo -e "\n${GREEN}${BOLD}✓ Setup complete!${NC}\n"
echo -e "${BOLD}To run the server, follow these steps:${NC}\n"

echo -e "${YELLOW}1. Set your DevRev API key:${NC}"
echo -e "   export DEVREV_API_KEY=\"your_api_key_here\"\n"

echo -e "${YELLOW}2. Activate the virtual environment:${NC}"
echo -e "   source venv/bin/activate\n"

echo -e "${YELLOW}3. Start the server:${NC}"
echo -e "   devrev-mcp\n"

echo -e "The server will be available at http://127.0.0.1:8888\n"

echo -e "${BLUE}${BOLD}Advanced Configuration (Optional):${NC}\n"
echo -e "You can customize the server behavior using environment variables:"
echo -e "  DEVREV_MCP_HOST      - Host address (default: 127.0.0.1)"
echo -e "  DEVREV_MCP_PORT      - Port number (default: 8888)"
echo -e "  DEVREV_MCP_LOG_LEVEL - Logging level (default: info)"
echo -e "  DEVREV_MCP_DEBUG     - Debug mode (default: false)"
echo -e "  DEVREV_API_BASE_URL  - DevRev API URL (default: https://api.devrev.ai)"
echo -e "  DEVREV_API_TIMEOUT   - API request timeout in seconds (default: 30)"
echo -e "  DEVREV_API_RETRIES   - Number of retry attempts for API calls (default: 3)"

echo -e "\n${BLUE}${BOLD}Integration with AI Assistants:${NC}\n"
echo -e "1. For Claude Desktop, add the following to your config:"
echo -e "   - macOS: ~/Library/Application\ Support/Claude/claude_desktop_config.json"
echo -e "   - Windows: %APPDATA%/Claude/claude_desktop_config.json\n"

echo -e '  "mcpServers": {'
echo -e '    "devrev": {'
echo -e '      "command": "'$(pwd)'/venv/bin/devrev-mcp",'
echo -e '      "env": {'
echo -e '        "DEVREV_API_KEY": "YOUR_DEVREV_API_KEY"'
echo -e '      }'
echo -e '    }'
echo -e '  }'

echo -e "\n2. For Cursor IDE, configure a new MCP server with:"
echo -e "   - Name: devrev"
echo -e "   - Command: $(pwd)/venv/bin/devrev-mcp"
echo -e "   - Environment: DEVREV_API_KEY=your_api_key_here"

echo -e "\n${GREEN}${BOLD}Happy querying with DevRev!${NC}" 