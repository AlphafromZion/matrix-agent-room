#!/usr/bin/env bash
# matrix-agent-room: Create Matrix accounts for AI bots
# Run this after Synapse is up and running.

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Create Bot Accounts                        ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env not found. Run setup.sh first.${NC}"
    exit 1
fi

# Source .env for the registration secret
# shellcheck disable=SC1091
source .env

SYNAPSE_CONTAINER="matrix-synapse"
HOMESERVER_URL="http://localhost:8008"

# Check if Synapse is running
if ! docker ps --format '{{.Names}}' | grep -q "^${SYNAPSE_CONTAINER}$"; then
    echo -e "${RED}✗ Synapse container not running. Start it first: docker compose up -d${NC}"
    exit 1
fi

echo -e "${CYAN}Synapse is running. Creating bot accounts...${NC}"
echo ""

# Function to create a bot account
create_bot() {
    local username="$1"
    local display_name="$2"

    # Generate a random password
    local password
    password=$(openssl rand -hex 16)

    echo -e "${CYAN}Creating account: ${username}${NC}"

    if docker exec "${SYNAPSE_CONTAINER}" register_new_matrix_user \
        -u "${username}" \
        -p "${password}" \
        --no-admin \
        -c /data/homeserver.yaml \
        "${HOMESERVER_URL}" 2>/dev/null; then

        echo -e "${GREEN}✓ Created @${username}${NC}"
        echo -e "  Password: ${password}"
        echo ""

        # Append password to .env
        local env_var
        env_var=$(echo "${username}" | tr '[:lower:]' '[:upper:]')_BOT_PASSWORD
        echo "${env_var}=${password}" >> .env
        echo -e "  → Added ${env_var} to .env"
    else
        echo -e "${YELLOW}⚠ Account @${username} may already exist (or registration failed)${NC}"
    fi
    echo ""
}

# --- Create your human admin account ---
echo -e "${YELLOW}First, let's create your admin account.${NC}"
read -rp "Admin username (e.g., admin): " ADMIN_USER
ADMIN_PASS=$(openssl rand -hex 16)

docker exec "${SYNAPSE_CONTAINER}" register_new_matrix_user \
    -u "${ADMIN_USER}" \
    -p "${ADMIN_PASS}" \
    -a \
    -c /data/homeserver.yaml \
    "${HOMESERVER_URL}" 2>/dev/null && \
    echo -e "${GREEN}✓ Admin account created: @${ADMIN_USER}${NC}" && \
    echo -e "  Password: ${ADMIN_PASS}" && \
    echo -e "  ${YELLOW}Save this password!${NC}" || \
    echo -e "${YELLOW}⚠ Admin account may already exist${NC}"

echo ""
echo -e "${CYAN}Creating bot accounts...${NC}"
echo ""

# --- Create bot accounts from config ---
# Default bots — customize these to match your config.yaml
create_bot "alpha" "Alpha 🐺"
create_bot "qwen" "Qwen 🔮"
create_bot "mistral" "Mistral ⚡"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════╗"
echo "║   Bot Accounts Created                       ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Bot passwords have been saved to .env"
echo ""
echo "Next steps:"
echo "1. Restart bots to pick up passwords: docker compose restart bots"
echo "2. Log into Element Web: http://localhost:8080"
echo "3. Create a room and invite the bots"
echo "4. Start chatting with @alpha, @qwen, @mistral!"
echo ""
echo -e "${GREEN}Your AI team is ready. 🤖${NC}"
